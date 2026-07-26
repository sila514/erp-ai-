"""
Tek bir ürün için talep tahmin modelini eğitir ve diske kaydeder.
Üretimde bu script bir zamanlanmış job (örn. günde bir kez, Airflow/Celery) ile çalıştırılır.
"""
import os

import joblib
from xgboost import XGBRegressor

from app.common.database import SessionLocal, settings
from app.demand_forecast.features import FEATURE_COLUMNS, build_features, load_daily_demand


def train_demand_model(product_id: str) -> str:
    db = SessionLocal()
    try:
        raw = load_daily_demand(db, product_id)
    finally:
        db.close()

    if raw.empty or len(raw) < 45:
        raise ValueError("Eğitim için yetersiz geçmiş veri (en az ~45 gün gerekli)")

    features = build_features(raw)
    X = features[FEATURE_COLUMNS]
    y = features["qty"]

    model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model.fit(X, y)

    os.makedirs(settings.MODEL_REGISTRY_PATH, exist_ok=True)
    model_path = os.path.join(settings.MODEL_REGISTRY_PATH, f"demand_{product_id}.joblib")
    joblib.dump(model, model_path)
    return model_path


if __name__ == "__main__":
    import sys

    train_demand_model(sys.argv[1])
