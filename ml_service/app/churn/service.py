"""
Müşteri churn olasılığını tahmin eder.
Gerçek projede model, geçmiş churn etiketli verilerle (örn. son 90 günde
hiç alışveriş yapmamış = churn) eğitilip diske kaydedilir.
Burada yapı gösterimi için basitleştirilmiş kural+model hibrit yaklaşım var.
"""
import os

import joblib
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.database import settings

MODEL_FILENAME = "churn_model.joblib"
FEATURE_COLUMNS = ["recency_days", "frequency", "avg_order_value", "days_since_signup"]


def _model_path() -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, MODEL_FILENAME)


def _get_customer_features(db: Session, customer_id: str) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                EXTRACT(DAY FROM NOW() - MAX(s.created_at)) AS recency_days,
                COUNT(s.id) AS frequency,
                COALESCE(AVG(s.total_amount), 0) AS avg_order_value,
                EXTRACT(DAY FROM NOW() - c.created_at) AS days_since_signup
            FROM customers c
            LEFT JOIN sales s ON s.customer_id = c.id
            WHERE c.id = :cid
            GROUP BY c.id, c.created_at
            """
        ),
        {"cid": customer_id},
    ).fetchone()
    if not row:
        raise ValueError("Müşteri bulunamadı")
    return dict(zip(FEATURE_COLUMNS, [v or 0 for v in row]))


def predict_churn(db: Session, customer_id: str) -> dict:
    features = _get_customer_features(db, customer_id)
    path = _model_path()

    if os.path.exists(path):
        model = joblib.load(path)
        X = [[features[c] for c in FEATURE_COLUMNS]]
        probability = float(model.predict_proba(X)[0][1])
    else:
        # Model eğitilene kadar basit kural tabanlı fallback:
        # uzun süre alışveriş yapmamış + az sıklık = yüksek risk
        probability = min(1.0, features["recency_days"] / 180) * 0.7 + (
            0.3 if features["frequency"] <= 1 else 0.0
        )
        probability = round(min(probability, 0.98), 4)

    if probability >= 0.7:
        risk_level = "high"
    elif probability >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    top_factors = []
    if features["recency_days"] > 60:
        top_factors.append("uzun süredir alışveriş yapmıyor")
    if features["frequency"] <= 2:
        top_factors.append("düşük satın alma sıklığı")
    if not top_factors:
        top_factors.append("belirgin risk sinyali yok")

    return {
        "customer_id": customer_id,
        "churn_probability": probability,
        "risk_level": risk_level,
        "top_factors": top_factors,
    }
