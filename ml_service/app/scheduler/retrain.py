"""
Zamanlanmış model yeniden eğitimi: talep tahmini (ürün başına), churn ve
anomali tespiti modellerini sırayla yeniden eğitir. Her ürün/model kendi
try/except'iyle izole edilir — biri başarısız olursa diğerleri çalışmaya
devam eder. CPU-yoğun .fit() çağrıları içerdiğinden, event loop'u
bloklamaması için çağıran taraf (app/scheduler/scheduler.py) bu modülün
fonksiyonlarını asyncio.to_thread ile sarmalamalıdır.
"""
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.anomaly_detection.train import train_anomaly_model
from app.churn.train import train_churn_model
from app.common.database import SessionLocal
from app.demand_forecast.train import train_demand_model

logger = logging.getLogger(__name__)

MIN_HISTORY_DAYS = 90  # train_demand_model ile tutarlı (bkz. demand_forecast/train.py)


def list_trainable_product_ids(db: Session, min_days: int = MIN_HISTORY_DAYS) -> list[str]:
    """movement_type='out' kayıtları en az `min_days` farklı güne yayılan ürün id'lerini döndürür."""
    query = text(
        """
        SELECT product_id
        FROM stock_movements
        WHERE movement_type = 'out'
        GROUP BY product_id
        HAVING COUNT(DISTINCT date_trunc('day', created_at)) >= :min_days
        """
    )
    rows = db.execute(query, {"min_days": min_days}).fetchall()
    return [str(row[0]) for row in rows]


def retrain_demand_forecast_models() -> dict:
    db = SessionLocal()
    try:
        product_ids = list_trainable_product_ids(db)
    finally:
        db.close()

    trained: list[str] = []
    failed: dict[str, str] = {}
    for product_id in product_ids:
        try:
            train_demand_model(product_id, report=True)
            trained.append(product_id)
        except Exception as exc:
            logger.exception("Talep tahmini yeniden eğitimi başarısız: product_id=%s", product_id)
            failed[product_id] = str(exc)
    return {"model": "demand_forecast", "trained": trained, "failed": failed}


def retrain_churn_model() -> dict:
    try:
        train_churn_model(report=True)
        return {"model": "churn", "trained": True, "failed": None}
    except Exception as exc:
        logger.exception("Churn modeli yeniden eğitimi başarısız")
        return {"model": "churn", "trained": False, "failed": str(exc)}


def retrain_anomaly_model() -> dict:
    try:
        train_anomaly_model(report=True)
        return {"model": "anomaly_detection", "trained": True, "failed": None}
    except Exception as exc:
        logger.exception("Anomali tespiti modeli yeniden eğitimi başarısız")
        return {"model": "anomaly_detection", "trained": False, "failed": str(exc)}


def run_scheduled_retraining() -> dict:
    """Üç modeli sırayla yeniden eğitir; senkron/bloklayıcıdır — çağıran taraf
    bunu ayrı bir thread'de (asyncio.to_thread) çalıştırmalıdır."""
    results = {
        "demand_forecast": retrain_demand_forecast_models(),
        "churn": retrain_churn_model(),
        "anomaly_detection": retrain_anomaly_model(),
    }
    n_products = len(results["demand_forecast"]["trained"]) + len(results["demand_forecast"]["failed"])
    n_failed = (
        len(results["demand_forecast"]["failed"])
        + int(bool(results["churn"]["failed"]))
        + int(bool(results["anomaly_detection"]["failed"]))
    )
    logger.info(
        "Zamanlanmış yeniden eğitim tamamlandı: %d üründen %d'i talep tahmini için başarılı, "
        "churn=%s, anomaly_detection=%s, toplam hata=%d",
        n_products,
        len(results["demand_forecast"]["trained"]),
        "ok" if not results["churn"]["failed"] else "FAILED",
        "ok" if not results["anomaly_detection"]["failed"] else "FAILED",
        n_failed,
    )
    return results
