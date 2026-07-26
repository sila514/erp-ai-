"""Analytics endpoint'leri için DB'den entity-özel sayısal DataFrame'ler yükler."""
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.calendar import is_holiday, is_weekend


def load_sales_features(db: Session, limit: int = 5000) -> pd.DataFrame:
    """Satış bazlı sayısal feature'lar — korelasyon matrisi `entity=sales` için."""
    rows = db.execute(
        text(
            """
            SELECT s.total_amount AS total_amount,
                   COALESCE(SUM(si.quantity), 0) AS item_count,
                   s.created_at AS created_at,
                   s.anomaly_score AS anomaly_score
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
            GROUP BY s.id, s.total_amount, s.created_at, s.anomaly_score
            ORDER BY s.created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()

    records = []
    for r in rows:
        d = r.created_at.date()
        records.append(
            {
                "total_amount": float(r.total_amount),
                "item_count": float(r.item_count),
                "hour_of_day": float(r.created_at.hour),
                "is_weekend": int(is_weekend(d)),
                "is_holiday": int(is_holiday(d)),
                "anomaly_score": float(r.anomaly_score) if r.anomaly_score is not None else None,
            }
        )
    return pd.DataFrame(records)


def load_product_features(db: Session) -> pd.DataFrame:
    """Ürün bazlı sayısal feature'lar — korelasyon matrisi `entity=products` için."""
    rows = db.execute(
        text(
            """
            SELECT p.id AS product_id, p.unit_price, p.unit_cost, p.stock_quantity,
                   p.reorder_level, p.lead_time_days,
                   COALESCE(AVG(sm.quantity) FILTER (WHERE sm.movement_type = 'out'), 0) AS avg_daily_demand,
                   COALESCE(STDDEV(sm.quantity) FILTER (WHERE sm.movement_type = 'out'), 0) AS demand_std
            FROM products p
            LEFT JOIN stock_movements sm ON sm.product_id = p.id
            GROUP BY p.id
            """
        )
    ).fetchall()
    return pd.DataFrame(
        [
            {
                "unit_price": float(r.unit_price),
                "unit_cost": float(r.unit_cost),
                "stock_quantity": float(r.stock_quantity),
                "reorder_level": float(r.reorder_level),
                "lead_time_days": float(r.lead_time_days),
                "avg_daily_demand": float(r.avg_daily_demand),
                "demand_std": float(r.demand_std or 0),
            }
            for r in rows
        ]
    )
