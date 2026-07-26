"""
Churn feature engineering: RFM + trend (son 90 gün / önceki 90 gün harcama
oranı) + kategori çeşitliliği + ödeme/davranış riski (anomali oranı) + tenure.

Aynı `build_customer_features` fonksiyonu hem eğitim (geçmiş bir snapshot
tarihinden, gerçek gelecekteki etiketle) hem de canlı skorlama (bugünden,
etiket bilinmez — tahmin edilen şey odur) için kullanılır; tek fark verilen
`snapshot_date` parametresi.
"""
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "avg_order_value",
    "monetary_total",
    "trend_ratio",
    "category_diversity",
    "anomaly_ratio",
    "tenure_days",
]


def build_customer_features(db: Session, snapshot_date: datetime) -> pd.DataFrame:
    """`snapshot_date`'ten önceki (dahil) satış geçmişini kullanarak her müşteri
    için RFM + davranışsal feature'ları hesaplar. Henüz o tarihte var olmayan
    müşteriler (created_at > snapshot) dahil edilmez."""
    d90_start = snapshot_date - timedelta(days=90)
    d180_start = snapshot_date - timedelta(days=180)

    query = text(
        """
        SELECT
            c.id AS customer_id,
            c.created_at AS signup_at,
            MAX(s.created_at) AS last_purchase_at,
            COUNT(s.id) AS frequency,
            COALESCE(SUM(s.total_amount), 0) AS monetary_total,
            COALESCE(AVG(s.total_amount), 0) AS avg_order_value,
            COALESCE(SUM(CASE WHEN s.created_at > :d90_start THEN s.total_amount ELSE 0 END), 0) AS spend_last_90,
            COALESCE(SUM(CASE WHEN s.created_at > :d180_start AND s.created_at <= :d90_start THEN s.total_amount ELSE 0 END), 0) AS spend_prev_90,
            COALESCE(SUM(CASE WHEN s.is_flagged_anomaly THEN 1 ELSE 0 END), 0) AS anomaly_count,
            COUNT(DISTINCT p.category) AS category_diversity
        FROM customers c
        LEFT JOIN sales s ON s.customer_id = c.id AND s.created_at <= :snapshot
        LEFT JOIN sale_items si ON si.sale_id = s.id
        LEFT JOIN products p ON p.id = si.product_id
        WHERE c.created_at <= :snapshot
        GROUP BY c.id, c.created_at
        """
    )
    rows = db.execute(
        query, {"snapshot": snapshot_date, "d90_start": d90_start, "d180_start": d180_start}
    ).fetchall()

    records = []
    for r in rows:
        last_purchase_at = r.last_purchase_at
        recency_days = (snapshot_date - last_purchase_at).days if last_purchase_at else 9999
        tenure_days = (snapshot_date - r.signup_at).days if r.signup_at else 0

        if r.spend_prev_90 > 0:
            trend_ratio = float(r.spend_last_90 / r.spend_prev_90)
        else:
            trend_ratio = 1.0 if r.spend_last_90 == 0 else 2.0
        anomaly_ratio = (r.anomaly_count / r.frequency) if r.frequency > 0 else 0.0

        records.append(
            {
                "customer_id": str(r.customer_id),
                "recency_days": float(recency_days),
                "frequency": int(r.frequency),
                "avg_order_value": float(r.avg_order_value),
                "monetary_total": float(r.monetary_total),
                "trend_ratio": trend_ratio,
                "category_diversity": int(r.category_diversity),
                "anomaly_ratio": float(anomaly_ratio),
                "tenure_days": float(tenure_days),
            }
        )
    return pd.DataFrame.from_records(records)


def label_churn(db: Session, snapshot_date: datetime, horizon_days: int = 90) -> pd.DataFrame:
    """(snapshot_date, snapshot_date+horizon_days] aralığında satın alma
    olmayan müşteriler için churn=1 — sadece gerçekleşmiş gelecekteki satışlara
    bakar, feature hesaplamasına karışmadığı için leakage yoktur."""
    window_end = snapshot_date + timedelta(days=horizon_days)
    query = text(
        """
        SELECT c.id AS customer_id,
               CASE WHEN EXISTS (
                   SELECT 1 FROM sales s
                   WHERE s.customer_id = c.id AND s.created_at > :snapshot AND s.created_at <= :window_end
               ) THEN 0 ELSE 1 END AS churn
        FROM customers c
        WHERE c.created_at <= :snapshot
        """
    )
    rows = db.execute(query, {"snapshot": snapshot_date, "window_end": window_end}).fetchall()
    return pd.DataFrame([{"customer_id": str(r.customer_id), "churn": int(r.churn)} for r in rows])
