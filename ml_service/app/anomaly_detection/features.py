"""
Anomali tespiti için satış feature'ları: tutar, kalem adedi, saat, hafta sonu
mü. Eğitim (geçmiş toplu veri) ve canlı skorlama (tek satış) aynı feature
tanımını kullanır ki model tutarlı çalışsın.
"""
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

FEATURE_COLUMNS = ["total_amount", "item_count", "hour_of_day", "is_weekend"]


def load_historical_sales_features(db: Session, limit: int = 5000) -> np.ndarray:
    rows = db.execute(
        text(
            """
            SELECT s.total_amount AS total_amount,
                   COALESCE(SUM(si.quantity), 1) AS item_count,
                   EXTRACT(HOUR FROM s.created_at) AS hour_of_day,
                   CASE WHEN EXTRACT(DOW FROM s.created_at) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
            GROUP BY s.id, s.total_amount, s.created_at
            ORDER BY s.created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()
    if not rows:
        return np.empty((0, len(FEATURE_COLUMNS)))
    return np.array(
        [[float(r.total_amount), float(r.item_count), float(r.hour_of_day), float(r.is_weekend)] for r in rows]
    )
