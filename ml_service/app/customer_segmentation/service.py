"""
RFM (Recency, Frequency, Monetary) feature'larına dayalı K-Means segmentasyonu.
Üretimde model periyodik olarak (örn. haftalık) yeniden eğitilip
customers.segment kolonuna yazılır.
"""
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text
from sqlalchemy.orm import Session

SEGMENT_LABELS = {0: "sadık_müşteri", 1: "yeni_müşteri", 2: "risk_altında", 3: "yüksek_değerli"}


def build_rfm(db: Session) -> pd.DataFrame:
    query = text(
        """
        SELECT
            c.id AS customer_id,
            EXTRACT(DAY FROM NOW() - MAX(s.created_at)) AS recency,
            COUNT(s.id) AS frequency,
            COALESCE(SUM(s.total_amount), 0) AS monetary
        FROM customers c
        LEFT JOIN sales s ON s.customer_id = c.id
        GROUP BY c.id
        """
    )
    rows = db.execute(query).fetchall()
    return pd.DataFrame(rows, columns=["customer_id", "recency", "frequency", "monetary"]).fillna(0)


def run_segmentation(db: Session, n_clusters: int = 4) -> list[dict]:
    df = build_rfm(db)
    if df.empty or len(df) < n_clusters:
        return []

    features = df[["recency", "frequency", "monetary"]]
    scaled = StandardScaler().fit_transform(features)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = model.fit_predict(scaled)
    df["segment"] = df["cluster"].map(SEGMENT_LABELS).fillna("diğer")

    return df[["customer_id", "segment", "recency", "frequency", "monetary"]].to_dict(orient="records")
