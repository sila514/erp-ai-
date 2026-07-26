"""
Segmentasyon modeli diske kaydedilmez (canlı RFM'e göre ucuza yeniden
hesaplanır), ama silhouette/elbow tanıları ve otomatik atanan segment
isimlerini raporlamak + model_cards/segmentation.md yazmak için bu script
kullanılır: python -m app.customer_segmentation.train --report
"""
import os
from collections import Counter
from datetime import datetime, timezone

import mlflow

from app.common.database import SessionLocal
from app.common.mlflow_utils import configure_mlflow
from app.customer_segmentation.service import run_segmentation_with_diagnostics

MODEL_CARD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "model_cards", "segmentation.md"
)


def run_report() -> dict:
    db = SessionLocal()
    try:
        records, diagnostics = run_segmentation_with_diagnostics(db)
    finally:
        db.close()

    if not records:
        raise ValueError("Segmentasyon için yetersiz müşteri verisi")

    segment_counts = Counter(r["segment"] for r in records)
    print(f"\n=== Segmentasyon — k=2..8 silhouette taraması (n={len(records)} müşteri) ===")
    for k, score in diagnostics["silhouette_scores"].items():
        marker = "  <-- seçilen k" if k == diagnostics["best_k"] else ""
        print(f"k={k}: silhouette={score:.3f}, inertia={diagnostics['inertias'][k]:.1f}{marker}")
    print(f"\nOtomatik atanan segmentler: {dict(segment_counts)}")

    _log_to_mlflow(records, diagnostics, segment_counts)
    _write_model_card(records, diagnostics, segment_counts)
    return {"diagnostics": diagnostics, "segment_counts": dict(segment_counts)}


def _log_to_mlflow(records, diagnostics: dict, segment_counts: Counter) -> None:
    configure_mlflow("segmentation")
    with mlflow.start_run(run_name=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")):
        mlflow.log_param("n_customers", len(records))
        mlflow.log_param("best_k", diagnostics["best_k"])
        mlflow.log_metric("silhouette_at_best_k", diagnostics["silhouette_at_best_k"])
        for k, score in diagnostics["silhouette_scores"].items():
            mlflow.log_metric(f"silhouette_k{k}", score)
        for segment, count in segment_counts.items():
            mlflow.log_metric(f"segment_count_{segment}", count)


def _write_model_card(records, diagnostics, segment_counts) -> None:
    os.makedirs(os.path.dirname(MODEL_CARD_PATH), exist_ok=True)
    lines = [
        "# Model Card — Müşteri Segmentasyonu",
        "",
        f"**Son güncelleme**: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Veri",
        f"- Örneklem: {len(records)} müşteri, RFM (recency/frequency/monetary) feature'ları.",
        "",
        "## Yöntem",
        "- K-Means, k=2..8 aralığında taranır; **silhouette score argmax** ile otomatik k seçilir "
        "(elbow/inertia eğrisi de hesaplanır, ama öznel olduğu için sadece bilgi amaçlıdır).",
        "- Küme etiketleri hardcoded değildir: her kümenin z-skor merkezleri "
        "(düşük recency + yüksek frequency/monetary → sadık_müşteri; yüksek monetary + düşük "
        "tenure → yüksek_değerli; düşük frequency + düşük tenure → yeni_müşteri; yüksek recency → "
        "risk_altında) ile karşılaştırılır; eşleşmeyen kümeler `segment_N` kalır.",
        "",
        "## Sonuçlar",
        "",
        "| k | Silhouette | Inertia |",
        "|---|---|---|",
    ]
    for k, score in diagnostics["silhouette_scores"].items():
        marker = " (seçilen)" if k == diagnostics["best_k"] else ""
        lines.append(f"| {k}{marker} | {score:.3f} | {diagnostics['inertias'][k]:.1f} |")

    lines += [
        "",
        f"**Seçilen k**: {diagnostics['best_k']} (silhouette={diagnostics['silhouette_at_best_k']:.3f})",
        "",
        f"**Otomatik atanan segment dağılımı**: {dict(segment_counts)}",
        "",
        "## Sınırlılıklar",
        "- Segmentasyon modeli diske kaydedilmez; her istek/rapor çalıştırıldığında canlı RFM "
        "üzerinden yeniden hesaplanır (müşteri sayısı arttıkça maliyeti gözden geçirilmeli).",
        "- Otomatik isimlendirme z-skor eşiklerine (±0.3) dayanır; küme merkezleri bu eşiklerin "
        "hiçbirini net geçmezse `segment_N` gibi genel bir isim kalır — bu beklenen bir davranıştır.",
        "",
    ]
    with open(MODEL_CARD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    run_report()
