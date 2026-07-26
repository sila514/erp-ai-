"""
Yeni bir satış işlemini, geçmiş işlem dağılımına göre anomali olup olmadığı
açısından skorlar. Önce kayıtlı (train.py ile eğitilmiş, contamination'ı
precision@k ile ayarlanmış) model yüklenir — tutarlı ve hızlıdır; henüz
eğitilmemişse geçmiş kayıtlarla anlık (on-the-fly) fit eden fallback'e düşülür.
"""
import os
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.anomaly_detection.features import load_historical_sales_features
from app.common.database import settings


def _model_path() -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, "anomaly_model.joblib")


def _resolve_feature_vector(db: Session, payload: dict) -> np.ndarray:
    """Payload'daki sale_id üzerinden gerçek created_at'i çekip hour/is_weekend
    feature'larını eğitimdekiyle aynı tanımla tutarlı hesaplar."""
    sale_id = payload.get("sale_id")
    hour_of_day, is_weekend = None, None
    if sale_id:
        row = db.execute(
            text(
                "SELECT EXTRACT(HOUR FROM created_at) AS h, EXTRACT(DOW FROM created_at) AS dow "
                "FROM sales WHERE id = :id"
            ),
            {"id": sale_id},
        ).fetchone()
        if row:
            hour_of_day = float(row.h)
            is_weekend = 1.0 if int(row.dow) in (0, 6) else 0.0

    if hour_of_day is None:
        now = datetime.now(timezone.utc)
        hour_of_day = float(now.hour)
        is_weekend = 1.0 if now.weekday() >= 5 else 0.0

    return np.array(
        [[float(payload["total_amount"]), float(payload.get("item_count", 1)), hour_of_day, is_weekend]]
    )


def check_anomaly(db: Session, payload: dict) -> dict:
    new_point = _resolve_feature_vector(db, payload)
    model_path = _model_path()

    if os.path.exists(model_path):
        model = joblib.load(model_path)
    else:
        history = load_historical_sales_features(db, limit=500)
        if history.shape[0] < 20:
            return {"is_anomaly": False, "anomaly_score": 0.0, "reason": "yetersiz_geçmiş_veri"}
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(history)

    score = model.decision_function(new_point)[0]  # düşük skor = daha anormal
    is_anomaly = bool(model.predict(new_point)[0] == -1)
    normalized_score = float(max(0.0, min(1.0, 0.5 - score)))

    return {"is_anomaly": is_anomaly, "anomaly_score": round(normalized_score, 4)}
