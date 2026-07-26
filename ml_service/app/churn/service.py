"""
Müşteri churn olasılığını tahmin eder. Eğitilmiş XGBoost modeli + F1-optimal
eşik (train.py tarafından üretilir) kullanılır; model henüz eğitilmemişse
basit kural tabanlı fallback'e düşülür. `top_factors`, eğitilmiş model varsa
gerçek SHAP (TreeExplainer) katkılarından üretilir.
"""
import os
from datetime import datetime, timezone

import joblib
import numpy as np
import shap
from sqlalchemy.orm import Session

from app.churn.feature_engineering import FEATURE_COLUMNS, build_customer_features
from app.common.database import settings

FEATURE_LABELS_TR = {
    "recency_days": "son alışverişten bu yana geçen gün sayısı",
    "frequency": "toplam satın alma sıklığı",
    "avg_order_value": "ortalama sepet tutarı",
    "monetary_total": "toplam harcama",
    "trend_ratio": "son 90 gün / önceki 90 gün harcama oranı",
    "category_diversity": "satın alınan kategori çeşitliliği",
    "anomaly_ratio": "anomali işaretli satış oranı",
    "tenure_days": "müşteri olma süresi (gün)",
}


def _model_path() -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, "churn_model.joblib")


def _threshold_path() -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, "churn_threshold.joblib")


def predict_churn(db: Session, customer_id: str) -> dict:
    snapshot_date = datetime.now(timezone.utc)
    features_df = build_customer_features(db, snapshot_date)
    row = features_df[features_df["customer_id"] == str(customer_id)]
    if row.empty:
        raise ValueError("Müşteri bulunamadı")
    features = row.iloc[0].to_dict()

    model_path = _model_path()
    X = np.array([[features[c] for c in FEATURE_COLUMNS]], dtype=float)

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        probability = float(model.predict_proba(X)[0][1])
        threshold = joblib.load(_threshold_path()) if os.path.exists(_threshold_path()) else 0.5

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)[0]
        contributions = sorted(zip(FEATURE_COLUMNS, shap_values), key=lambda kv: abs(kv[1]), reverse=True)
        top_factors = [
            f"{FEATURE_LABELS_TR.get(name, name)} ({'risk artırıcı' if val > 0 else 'risk azaltıcı'})"
            for name, val in contributions[:3]
            if abs(val) > 1e-4
        ]
        if not top_factors:
            top_factors = ["belirgin risk sinyali yok"]
    else:
        # Model eğitilene kadar basit kural tabanlı fallback
        probability = min(1.0, features["recency_days"] / 180) * 0.7 + (
            0.3 if features["frequency"] <= 1 else 0.0
        )
        probability = round(min(probability, 0.98), 4)
        threshold = 0.5
        top_factors = []
        if features["recency_days"] > 60:
            top_factors.append("uzun süredir alışveriş yapmıyor")
        if features["frequency"] <= 2:
            top_factors.append("düşük satın alma sıklığı")
        if not top_factors:
            top_factors.append("belirgin risk sinyali yok (kural tabanlı fallback — model henüz eğitilmedi)")

    # risk_level, F1-optimal eşiği referans alır: eşiğin altı düşük, eşik ile
    # eşik+kalan aralığının yarısı arası orta, üstü yüksek risk.
    high_cutoff = threshold + (1 - threshold) / 2
    if probability >= high_cutoff:
        risk_level = "high"
    elif probability >= threshold:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "customer_id": str(customer_id),
        "churn_probability": round(probability, 4),
        "risk_level": risk_level,
        "top_factors": top_factors,
    }
