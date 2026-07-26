import math

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.demand_forecast.predict import predict_demand


def _get_product_stock_info(db: Session, product_id: str) -> dict:
    row = db.execute(
        text("SELECT stock_quantity, lead_time_days, reorder_level FROM products WHERE id = :pid"),
        {"pid": product_id},
    ).fetchone()
    if not row:
        raise ValueError("Ürün bulunamadı")
    return {"stock_quantity": row[0], "lead_time_days": row[1], "reorder_level": row[2]}


def compute_stock_risk(db: Session, product_id: str) -> dict:
    product_info = _get_product_stock_info(db, product_id)

    try:
        forecast = predict_demand(db, product_id, horizon_days=30)
        avg_daily_demand = forecast["average_daily_demand"]
    except (FileNotFoundError, ValueError):
        # Model henüz eğitilmemişse basit ortalamaya düş (fallback)
        avg_daily_demand = 1.0

    current_stock = product_info["stock_quantity"]
    lead_time = product_info["lead_time_days"]

    days_until_stockout = current_stock / avg_daily_demand if avg_daily_demand > 0 else math.inf

    if days_until_stockout <= lead_time:
        risk_level = "high"
    elif days_until_stockout <= lead_time * 2:
        risk_level = "medium"
    else:
        risk_level = "low"

    recommended_reorder = max(0, math.ceil(avg_daily_demand * lead_time * 1.5) - current_stock)

    return {
        "product_id": product_id,
        "current_stock": current_stock,
        "predicted_daily_demand": round(avg_daily_demand, 2),
        "days_until_stockout": round(days_until_stockout, 1) if days_until_stockout != math.inf else None,
        "risk_level": risk_level,
        "recommended_reorder_quantity": recommended_reorder,
    }
