"""
Stok riski: talep tahmininin belirsizliğini (p10/p90 aralığı) kullanarak
güvenlik stoğu hesaplar. safety_stock = z(service_level) * sigma * sqrt(lead_time_days)
— klasik envanter teorisi formülü. `service_level` (varsayılan %95) yükseldikçe
z-skoru büyür, daha fazla güvenlik stoğu önerilir.
"""
import math

import numpy as np
from scipy.stats import norm
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.demand_forecast.predict import predict_demand

# p90-p10 aralığından sigma tahmini: standart normal dağılımda p90-p10 farkı 2*1.2816*sigma'dır.
_P10_P90_TO_SIGMA = 2 * norm.ppf(0.90)


def _get_product_stock_info(db: Session, product_id: str) -> dict:
    row = db.execute(
        text("SELECT stock_quantity, lead_time_days, reorder_level FROM products WHERE id = :pid"),
        {"pid": product_id},
    ).fetchone()
    if not row:
        raise ValueError("Ürün bulunamadı")
    return {"stock_quantity": row[0], "lead_time_days": row[1], "reorder_level": row[2]}


def compute_stock_risk(db: Session, product_id: str, service_level: float = 0.95) -> dict:
    if not 0.5 < service_level < 0.999:
        raise ValueError("service_level 0.5 ile 0.999 arasında olmalı")

    product_info = _get_product_stock_info(db, product_id)
    current_stock = product_info["stock_quantity"]
    lead_time = product_info["lead_time_days"]

    try:
        forecast = predict_demand(db, product_id, horizon_days=30)
        avg_daily_demand = forecast["average_daily_demand"]
        p10 = np.array(forecast["predicted_daily_demand_p10"])
        p90 = np.array(forecast["predicted_daily_demand_p90"])
        daily_sigma = float(np.mean(np.maximum(p90 - p10, 0.0)) / _P10_P90_TO_SIGMA)
        uncertainty_source = "quantile_forecast"
    except (FileNotFoundError, ValueError):
        # Model henüz eğitilmemişse basit ortalamaya ve kaba bir belirsizlik varsayımına düş
        avg_daily_demand = 1.0
        daily_sigma = avg_daily_demand * 0.3  # %30 değişkenlik katsayısı varsayımı
        uncertainty_source = "fallback_cv_30pct"

    z = float(norm.ppf(service_level))
    safety_stock = z * daily_sigma * math.sqrt(max(lead_time, 0))
    reorder_point = avg_daily_demand * lead_time + safety_stock

    days_until_stockout = current_stock / avg_daily_demand if avg_daily_demand > 0 else math.inf

    if days_until_stockout <= lead_time:
        risk_level = "high"
    elif days_until_stockout <= lead_time * 2:
        risk_level = "medium"
    else:
        risk_level = "low"

    recommended_reorder = max(0, math.ceil(reorder_point - current_stock))

    return {
        "product_id": product_id,
        "current_stock": current_stock,
        "predicted_daily_demand": round(avg_daily_demand, 2),
        "daily_demand_sigma": round(daily_sigma, 2),
        "days_until_stockout": round(days_until_stockout, 1) if days_until_stockout != math.inf else None,
        "risk_level": risk_level,
        "service_level": service_level,
        "safety_stock": round(safety_stock, 1),
        "reorder_point": round(reorder_point, 1),
        "recommended_reorder_quantity": recommended_reorder,
        "uncertainty_source": uncertainty_source,
    }
