import os

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.common.database import settings
from app.demand_forecast.features import FEATURE_COLUMNS, build_features, load_daily_demand


def _model_path(product_id: str) -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, f"demand_{product_id}.joblib")


def predict_demand(db: Session, product_id, horizon_days: int = 30) -> dict:
    """
    Eğitilmiş modeli kullanarak ileri günler için talep tahmini üretir.
    Basitlik için: son bilinen feature satırını alıp horizon boyunca
    tek adım ileri tahmin + feature güncelleme (recursive forecasting) yapar.
    """
    path = _model_path(str(product_id))
    if not os.path.exists(path):
        raise FileNotFoundError(
            "Bu ürün için eğitilmiş model bulunamadı. Önce train_demand_model çalıştırılmalı."
        )

    model = joblib.load(path)
    raw = load_daily_demand(db, product_id)
    features = build_features(raw)

    history = list(features["qty"].values)
    predictions = []

    for _ in range(horizon_days):
        last_row = {
            "lag_1": history[-1],
            "lag_7": history[-7] if len(history) >= 7 else history[-1],
            "rolling_mean_7": float(np.mean(history[-7:])),
            "rolling_mean_30": float(np.mean(history[-30:])),
            "day_of_week": 0,  # basitleştirilmiş; gerçek tarihten hesaplanmalı
            "day_of_month": 1,
        }
        X = [[last_row[c] for c in FEATURE_COLUMNS]]
        pred = float(model.predict(X)[0])
        pred = max(pred, 0.0)
        predictions.append(pred)
        history.append(pred)

    return {
        "product_id": str(product_id),
        "horizon_days": horizon_days,
        "predicted_daily_demand": predictions,
        "average_daily_demand": float(np.mean(predictions)),
    }
