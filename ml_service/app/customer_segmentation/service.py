"""
RFM (Recency, Frequency, Monetary) feature'larına dayalı K-Means segmentasyonu.
Küme sayısı (k) sabit değil — k=2..8 aralığında silhouette score ile otomatik
seçilir (elbow/inertia eğrisi de hesaplanır, ama otomatik seçim silhouette
argmax ile yapılır; elbow görsel/öznel olduğu için sadece raporlama amaçlı).

Kümeler, merkezlerinin (StandardScaler sonrası, yani zaten z-skor olan)
recency/frequency/monetary değerleri + üyelerin ortalama tenure'ı arketipsel
örüntülerle karşılaştırılarak otomatik isimlendirilir — hardcoded segment
haritası yoktur; eşleşmeyen kümeler `segment_N` olarak kalır.

Üretimde bu, periyodik olarak (örn. haftalık) yeniden çalıştırılıp
customers.segment kolonuna yazılır.
"""
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text
from sqlalchemy.orm import Session

RFM_COLUMNS = ["recency", "frequency", "monetary"]
Z_THRESHOLD = 0.3  # bir z-skorun "belirgin şekilde yüksek/düşük" sayılması için eşik
K_RANGE = range(2, 9)


def build_rfm(db: Session) -> pd.DataFrame:
    query = text(
        """
        SELECT
            c.id AS customer_id,
            EXTRACT(DAY FROM NOW() - MAX(s.created_at)) AS recency,
            COUNT(s.id) AS frequency,
            COALESCE(SUM(s.total_amount), 0) AS monetary,
            EXTRACT(DAY FROM NOW() - c.created_at) AS tenure_days
        FROM customers c
        LEFT JOIN sales s ON s.customer_id = c.id
        GROUP BY c.id, c.created_at
        """
    )
    rows = db.execute(query).fetchall()
    df = pd.DataFrame(rows, columns=["customer_id", "recency", "frequency", "monetary", "tenure_days"]).fillna(0)
    for col in ["recency", "frequency", "monetary", "tenure_days"]:
        df[col] = df[col].astype(float)
    return df


def select_optimal_k(scaled_features) -> tuple[int, dict[int, float], dict[int, float]]:
    """k=2..8 aralığında silhouette score hesaplar, argmax olan k'yı döndürür.
    Inertia (elbow eğrisi) da hesaplanır, sadece raporlama/model_card amaçlı."""
    silhouette_scores: dict[int, float] = {}
    inertias: dict[int, float] = {}
    n_samples = len(scaled_features)

    for k in K_RANGE:
        if k >= n_samples:
            break
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(scaled_features)
        inertias[k] = float(model.inertia_)
        silhouette_scores[k] = float(silhouette_score(scaled_features, labels))

    best_k = max(silhouette_scores, key=silhouette_scores.get)
    return best_k, silhouette_scores, inertias


def label_clusters(df: pd.DataFrame, cluster_col: str = "cluster") -> dict[int, str]:
    """Küme merkezlerinin z-skorlarına (recency/frequency/monetary, StandardScaler
    çıktısından) ve üye ortalama tenure z-skoruna göre arketipsel isim atar."""
    tenure_mean = df["tenure_days"].mean()
    tenure_std = df["tenure_days"].std() or 1.0

    labels: dict[int, str] = {}
    for cluster_id, group in df.groupby(cluster_col):
        recency_z = group["recency_z"].mean()
        frequency_z = group["frequency_z"].mean()
        monetary_z = group["monetary_z"].mean()
        tenure_z = (group["tenure_days"].mean() - tenure_mean) / tenure_std

        if recency_z < -Z_THRESHOLD and frequency_z > Z_THRESHOLD and monetary_z > Z_THRESHOLD:
            labels[cluster_id] = "sadık_müşteri"
        elif monetary_z > Z_THRESHOLD and tenure_z < -Z_THRESHOLD:
            labels[cluster_id] = "yüksek_değerli"
        elif frequency_z < -Z_THRESHOLD and tenure_z < -Z_THRESHOLD:
            labels[cluster_id] = "yeni_müşteri"
        elif recency_z > Z_THRESHOLD:
            labels[cluster_id] = "risk_altında"
        else:
            labels[cluster_id] = f"segment_{cluster_id}"
    return labels


def _fit_segmentation(df: pd.DataFrame):
    features = df[RFM_COLUMNS]
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    best_k, silhouette_scores, inertias = select_optimal_k(scaled)

    model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    df = df.copy()
    df["cluster"] = model.fit_predict(scaled)
    df["recency_z"] = scaled[:, 0]
    df["frequency_z"] = scaled[:, 1]
    df["monetary_z"] = scaled[:, 2]

    cluster_labels = label_clusters(df)
    df["segment"] = df["cluster"].map(cluster_labels)

    diagnostics = {
        "best_k": best_k,
        "silhouette_scores": silhouette_scores,
        "inertias": inertias,
        "cluster_labels": cluster_labels,
        "silhouette_at_best_k": silhouette_scores[best_k],
    }
    return df, diagnostics


def run_segmentation(db: Session) -> list[dict]:
    df = build_rfm(db)
    if df.empty or len(df) < min(K_RANGE):
        return []
    df, _ = _fit_segmentation(df)
    return df[["customer_id", "segment", "recency", "frequency", "monetary"]].to_dict(orient="records")


def run_segmentation_with_diagnostics(db: Session) -> tuple[list[dict], dict]:
    """`run_segmentation` ile aynı, ama silhouette/inertia/otomatik etiket
    tanılarını da döndürür (model_card raporlaması için)."""
    df = build_rfm(db)
    if df.empty or len(df) < min(K_RANGE):
        return [], {}
    df, diagnostics = _fit_segmentation(df)
    records = df[["customer_id", "segment", "recency", "frequency", "monetary"]].to_dict(orient="records")
    return records, diagnostics
