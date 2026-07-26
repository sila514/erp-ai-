import os
from datetime import timedelta

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.common.database import settings
from app.demand_forecast.features import (
    FEATURE_COLUMNS,
    build_features,
    calendar_features_for_date,
    load_daily_demand,
)


def _model_path(product_id: str, quantile: str) -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, f"demand_{product_id}_{quantile}.joblib")


def predict_demand(db: Session, product_id, horizon_days: int = 30) -> dict:
    """
    Eğitilmiş p10/p50/p90 modellerini kullanarak ileri günler için talep tahmin
    aralığı üretir. Recursive forecasting: her adımda gerçek takvim tarihinden
    (son bilinen gün + adım sayısı) hesaplanan feature'lar kullanılır — önceki
    sürümdeki `day_of_week=0`/`day_of_month=1` hardcoded bug'ı burada düzeltildi.
    p50 tahminleri bir sonraki adımın lag/rolling feature'larını beslemek için
    geçmişe eklenir; p10/p90 sadece o adımın belirsizlik aralığını raporlar.
    """
    p50_path = _model_path(str(product_id), "p50")
    if not os.path.exists(p50_path):
        raise FileNotFoundError(
            "Bu ürün için eğitilmiş model bulunamadı. Önce train_demand_model çalıştırılmalı."
        )

    models = {}
    for q in ("p10", "p50", "p90"):
        path = _model_path(str(product_id), q)
        if os.path.exists(path):
            models[q] = joblib.load(path)

    raw = load_daily_demand(db, product_id)
    features = build_features(raw)

    history = list(features["qty"].values)
    last_date = features["day"].iloc[-1]

    predictions = {"p10": [], "p50": [], "p90": []}

    for step in range(1, horizon_days + 1):
        forecast_date = (last_date + timedelta(days=step)).date()
        cal = calendar_features_for_date(forecast_date)
        row = {
            "lag_1": history[-1],
            "lag_7": history[-7] if len(history) >= 7 else history[-1],
            "rolling_mean_7": float(np.mean(history[-7:])),
            "rolling_mean_30": float(np.mean(history[-30:])),
            **cal,
        }
        X = [[row[c] for c in FEATURE_COLUMNS]]

        step_preds = {}
        for q, model in models.items():
            step_preds[q] = max(float(model.predict(X)[0]), 0.0)

        p50 = step_preds.get("p50", next(iter(step_preds.values()), 0.0))
        for q in ("p10", "p50", "p90"):
            predictions[q].append(step_preds.get(q, p50))

        history.append(p50)

    return {
        "product_id": str(product_id),
        "horizon_days": horizon_days,
        "predicted_daily_demand": predictions["p50"],
        "predicted_daily_demand_p10": predictions["p10"],
        "predicted_daily_demand_p90": predictions["p90"],
        "average_daily_demand": float(np.mean(predictions["p50"])),
    }
