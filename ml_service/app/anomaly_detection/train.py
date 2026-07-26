"""
Anomali tespiti modelini eğitir: geçmiş satış feature'larıyla IsolationForest
fit edilip diske kaydedilir (artık her istekte yeniden fit edilmiyor).
`contamination` parametresi, gerçek veriye enjekte edilen sentetik aykırı
noktalarla oluşturulan (yalnızca değerlendirme amaçlı, DB'ye yazılmayan)
etiketli bir sette precision@k taranarak seçilir.

--report bayrağıyla model_cards/anomaly_detection.md yazılır.
"""
import os
from datetime import datetime, timezone

import joblib
import mlflow
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score

from app.anomaly_detection.features import FEATURE_COLUMNS, load_historical_sales_features
from app.common.database import SessionLocal, settings
from app.common.mlflow_utils import configure_mlflow

CONTAMINATION_CANDIDATES = [0.01, 0.02, 0.05, 0.08, 0.12, 0.18]
N_INJECTED_ANOMALIES = 40
RNG_SEED = 42

MODEL_CARD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "model_cards", "anomaly_detection.md"
)


def _model_path() -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, "anomaly_model.joblib")


def _inject_synthetic_anomalies(
    normal: np.ndarray, n: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Gerçek satırlardan rastgele seçip total_amount/item_count'u aşırı büyüterek
    sentetik, bariz aykırı noktalar üretir (yalnızca değerlendirme için — DB'ye yazılmaz)."""
    idx = rng.choice(len(normal), size=n, replace=True)
    synthetic = normal[idx].copy()
    synthetic[:, 0] *= rng.uniform(5, 15, size=n)  # total_amount
    synthetic[:, 1] *= rng.uniform(4, 10, size=n)  # item_count
    labels = np.concatenate([np.zeros(len(normal)), np.ones(n)])
    combined = np.vstack([normal, synthetic])
    return combined, labels


def _precision_at_k(scores: np.ndarray, labels: np.ndarray, k: int) -> float:
    """scores: düşük = daha anormal (decision_function çıktısı). En anormal k
    nokta içindeki gerçek (enjekte edilmiş) anomali oranı."""
    top_k_idx = np.argsort(scores)[:k]
    return float(labels[top_k_idx].sum() / k)


def train_anomaly_model(report: bool = False) -> dict:
    db = SessionLocal()
    try:
        history = load_historical_sales_features(db, limit=5000)
    finally:
        db.close()

    if len(history) < 100:
        raise ValueError("Eğitim için yetersiz geçmiş satış verisi (en az ~100 kayıt gerekli)")

    rng = np.random.default_rng(RNG_SEED)
    split = int(len(history) * 0.7)
    perm = rng.permutation(len(history))
    train_idx, eval_idx = perm[:split], perm[split:]
    train_data = history[train_idx]
    eval_normal = history[eval_idx]

    eval_data, eval_labels = _inject_synthetic_anomalies(eval_normal, N_INJECTED_ANOMALIES, rng)
    k = N_INJECTED_ANOMALIES

    # Sıralama kalitesi (contamination'dan bağımsız): decision_function skorlarına göre
    # en anormal k nokta içinde gerçek (enjekte edilmiş) anomali oranı. contamination sadece
    # predict()'in ikili -1/1 eşiğini (offset_) belirler, decision_function sıralamasını
    # etkilemez — bu yüzden contamination taraması ayrı, eşik-duyarlı bir metrikle yapılır.
    ranking_model = IsolationForest(contamination=0.05, random_state=42)
    ranking_model.fit(train_data)
    ranking_scores = ranking_model.decision_function(eval_data)
    precision_at_k = _precision_at_k(ranking_scores, eval_labels, k)

    # contamination taraması: her adayın kendi eşiğinde (predict() ikili kararı) F1
    contamination_results = {}
    for c in CONTAMINATION_CANDIDATES:
        model = IsolationForest(contamination=c, random_state=42)
        model.fit(train_data)
        preds = (model.predict(eval_data) == -1).astype(int)
        precision = precision_score(eval_labels, preds, zero_division=0)
        recall = recall_score(eval_labels, preds, zero_division=0)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        contamination_results[c] = {"precision": precision, "recall": recall, "f1": f1}

    best_contamination = max(contamination_results, key=lambda c: contamination_results[c]["f1"])

    # Üretim modeli: en iyi contamination ile TÜM geçmiş veride yeniden eğitilir
    final_model = IsolationForest(contamination=best_contamination, random_state=42)
    final_model.fit(history)

    os.makedirs(settings.MODEL_REGISTRY_PATH, exist_ok=True)
    joblib.dump(final_model, _model_path())

    result = {
        "n_historical": len(history),
        "precision_at_k": precision_at_k,
        "contamination_results": contamination_results,
        "best_contamination": best_contamination,
        "k": k,
    }

    if report:
        print(f"\n=== Anomali tespiti — sıralama kalitesi: precision@{k}={precision_at_k:.3f} (n_geçmiş={len(history)}) ===")
        print(f"\n=== contamination taraması (predict() eşiğinde precision/recall/F1) ===")
        for c, m in contamination_results.items():
            marker = "  <-- seçilen" if c == best_contamination else ""
            print(f"contamination={c}: precision={m['precision']:.3f} recall={m['recall']:.3f} f1={m['f1']:.3f}{marker}")
        _log_to_mlflow(result)
        _write_model_card(result)

    return result


def _log_to_mlflow(result: dict) -> None:
    configure_mlflow("anomaly_detection")
    with mlflow.start_run(run_name=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")):
        mlflow.log_param("n_historical", result["n_historical"])
        mlflow.log_param("best_contamination", result["best_contamination"])
        mlflow.log_metric("precision_at_k", result["precision_at_k"])
        best_metrics = result["contamination_results"][result["best_contamination"]]
        mlflow.log_metrics({f"best_{k}": v for k, v in best_metrics.items()})


def _write_model_card(result: dict) -> None:
    os.makedirs(os.path.dirname(MODEL_CARD_PATH), exist_ok=True)
    lines = [
        "# Model Card — Anomali Tespiti (Satış İşlemleri)",
        "",
        f"**Son güncelleme**: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Veri",
        f"- Geçmiş satış sayısı: {result['n_historical']}",
        f"- Feature'lar: {', '.join(FEATURE_COLUMNS)}",
        f"- Değerlendirme seti: gerçek verinin %30'luk tutma payına {N_INJECTED_ANOMALIES} sentetik "
        "aykırı nokta enjekte edilerek oluşturuldu (total_amount/item_count 4-15x büyütülerek — "
        "yalnızca değerlendirme amaçlı, gerçek veritabanına yazılmaz).",
        "",
        "## Yöntem",
        f"- Sıralama kalitesi: decision_function skorlarına göre en anormal {result['k']} nokta "
        "içindeki gerçek (enjekte edilmiş) anomali oranı — **precision@k** (contamination'dan "
        "bağımsız bir metrik, çünkü contamination sadece predict()'in ikili eşiğini belirler).",
        "- `contamination`, her adayın kendi predict() eşiğinde ölçülen precision/recall/F1 "
        "taranarak (F1-argmax) seçildi.",
        "- Üretim modeli, seçilen contamination ile TÜM geçmiş veride yeniden eğitilip diske "
        "kaydedildi (`anomaly_model.joblib`); canlı skorlama artık her istekte yeniden fit etmez.",
        "",
        "## Sonuçlar",
        "",
        f"**Sıralama kalitesi — precision@{result['k']}**: {result['precision_at_k']:.3f}",
        "",
        "| Contamination | Precision | Recall | F1 |",
        "|---|---|---|---|",
    ]
    for c, m in result["contamination_results"].items():
        marker = " (seçilen)" if c == result["best_contamination"] else ""
        lines.append(f"| {c}{marker} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} |")

    lines += [
        "",
        f"**Seçilen contamination**: {result['best_contamination']}",
        "",
        "## Sınırlılıklar",
        "- Değerlendirme etiketleri sentetik enjeksiyonla üretilmiştir; gerçek dolandırıcılık/hata "
        "örüntüleri farklı görünebilir, üretimde gerçek işaretlenmiş vakalar biriktikçe yeniden "
        "değerlendirilmelidir.",
        "- Model periyodik olarak (örn. haftalık) yeniden eğitilmelidir; bu script bir zamanlanmış "
        "job'a bağlanmalıdır.",
        "",
    ]
    with open(MODEL_CARD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    import sys

    train_anomaly_model(report="--report" in sys.argv)
