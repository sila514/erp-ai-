"""
Ürün bazlı talep tahmin modellerini eğitir: p10/p50/p90 quantile regression
(XGBoost native `reg:quantileerror`). Üretimde bu script bir zamanlanmış job
(örn. günde bir kez, Airflow/Celery) ile çalıştırılır.

--report bayrağıyla çalıştırıldığında expanding-window CV sonuçlarını konsola
basar ve model_cards/demand_forecast.md'ye yazar.
"""
import os
from datetime import datetime, timezone

import joblib
import mlflow
import numpy as np
from xgboost import XGBRegressor

from app.common.database import SessionLocal, settings
from app.common.mlflow_utils import configure_mlflow
from app.demand_forecast.evaluation import expanding_window_cv, format_cv_table
from app.demand_forecast.features import FEATURE_COLUMNS, build_features, load_daily_demand
from app.monitoring.drift import interpret_psi, ks_drift_test, population_stability_index

QUANTILES = {"p10": 0.10, "p50": 0.50, "p90": 0.90}
MODEL_CARD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "model_cards", "demand_forecast.md"
)
MODEL_PARAMS = dict(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8)


def _model_path(product_id: str, quantile: str) -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, f"demand_{product_id}_{quantile}.joblib")


def _reference_dist_path(product_id: str) -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, f"demand_{product_id}_reference_qty.npy")


def _check_drift(product_id: str, current_qty: np.ndarray) -> dict | None:
    """Önceki eğitimden kalan referans dağılımla PSI/KS karşılaştırması yapar;
    ilk eğitimde referans olmadığı için None döner. Karşılaştırma sonunda
    mevcut dağılım bir sonraki çalıştırma için referans olarak kaydedilir."""
    ref_path = _reference_dist_path(product_id)
    drift_result = None
    if os.path.exists(ref_path):
        reference = np.load(ref_path)
        psi = population_stability_index(reference, current_qty)
        ks = ks_drift_test(reference, current_qty)
        drift_result = {"psi": psi, "psi_interpretation": interpret_psi(psi), "ks": ks}
    np.save(ref_path, current_qty)
    return drift_result


def train_demand_model(product_id: str, report: bool = False) -> dict:
    db = SessionLocal()
    try:
        raw = load_daily_demand(db, product_id)
    finally:
        db.close()

    if raw.empty or len(raw) < 90:
        raise ValueError("Eğitim için yetersiz geçmiş veri (en az ~90 gün gerekli)")

    features = build_features(raw)
    X = features[FEATURE_COLUMNS]
    y = features["qty"]

    cv_result = None
    drift_result = None
    if report:
        cv_result = expanding_window_cv(features)
        print(f"\n=== Ürün {product_id} — Expanding-window CV sonuçları ===")
        print(format_cv_table(cv_result))

        drift_result = _check_drift(product_id, y.values)
        if drift_result:
            print(
                f"\nVeri drift kontrolü: PSI={drift_result['psi']:.4f} "
                f"({drift_result['psi_interpretation']}), "
                f"KS p-value={drift_result['ks']['p_value']:.4f} "
                f"(drifted={drift_result['ks']['drifted']})"
            )

    os.makedirs(settings.MODEL_REGISTRY_PATH, exist_ok=True)
    saved_paths = {}
    for name, alpha in QUANTILES.items():
        model = XGBRegressor(
            objective="reg:quantileerror",
            quantile_alpha=alpha,
            random_state=42,
            **MODEL_PARAMS,
        )
        model.fit(X, y)
        path = _model_path(product_id, name)
        joblib.dump(model, path)
        saved_paths[name] = path

    if report and cv_result is not None:
        _log_to_mlflow(product_id, cv_result, drift_result)
        _write_model_card(product_id, raw, cv_result, drift_result)

    return {"saved_paths": saved_paths, "cv_result": cv_result, "drift_result": drift_result}


def _log_to_mlflow(product_id: str, cv_result: dict, drift_result: dict | None) -> None:
    configure_mlflow("demand_forecast")
    with mlflow.start_run(run_name=f"product_{product_id}"):
        mlflow.log_params({**MODEL_PARAMS, "product_id": product_id, "n_folds": len(cv_result["folds"])})
        for model_name, metrics in cv_result["summary"].items():
            for metric_name, value in metrics.items():
                if metric_name != "n_folds":
                    mlflow.log_metric(f"{model_name}_{metric_name}", value)
        mlflow.log_metric("beats_best_baseline", int(cv_result["beats_best_baseline"]))
        if drift_result:
            mlflow.log_metric("drift_psi", drift_result["psi"])
            mlflow.log_metric("drift_ks_pvalue", drift_result["ks"]["p_value"])


def _write_model_card(product_id: str, raw, cv_result: dict, drift_result: dict | None = None) -> None:
    os.makedirs(os.path.dirname(MODEL_CARD_PATH), exist_ok=True)
    drift_section = "İlk eğitim — henüz referans dağılım yok."
    if drift_result:
        drift_section = (
            f"PSI={drift_result['psi']:.4f} ({drift_result['psi_interpretation']}), "
            f"KS p-value={drift_result['ks']['p_value']:.4f} (drifted={drift_result['ks']['drifted']})"
        )
    with open(MODEL_CARD_PATH, "w", encoding="utf-8") as f:
        f.write(
            f"""# Model Card — Talep Tahmini (Demand Forecast)

**Son güncelleme**: {datetime.now(timezone.utc).isoformat()}
**Örnek ürün**: {product_id}

## Veri
- Kaynak: `stock_movements` tablosu, `movement_type='out'`, günlük toplanmış miktar.
- Gözlem sayısı (feature engineering sonrası): {len(raw)} gün.
- Feature'lar: {", ".join(FEATURE_COLUMNS)}

## Yöntem
- Model: XGBoost regresyon, 3 ayrı quantile model (p10/p50/p90, `reg:quantileerror`).
- Değerlendirme: Expanding-window (walk-forward) time series CV, {len(cv_result["folds"])} katlama.
- Karşılaştırma: naive, seasonal_naive (7 gün), moving_average (7 gün) baseline'ları.
- Deney takibi: MLflow (`./mlruns`, `demand_forecast` experiment'i).

## Veri Drift Kontrolü
{drift_section}

## Sonuçlar (CV ortalaması)

```
{format_cv_table(cv_result)}
```

## Sınırlılıklar
- Quantile modeller her ürün için ayrı ayrı eğitilir; az sayıda geçmiş kaydı olan
  yeni ürünlerde güvenilirlik düşer (minimum ~90 gün geçmiş önerilir).
- p10/p90 aralığı XGBoost'un pinball-loss quantile regresyonundan gelir;
  kalibrasyonu (nominal %80 aralığın gerçek kapsama oranı) düzenli izlenmelidir.
- Kampanya/tatil gibi ekstrem olaylarda (eğitim verisinde az örnek) tahmin
  aralığı olduğundan dar kalabilir.
"""
        )


if __name__ == "__main__":
    import sys

    pid = sys.argv[1]
    do_report = "--report" in sys.argv
    result = train_demand_model(pid, report=do_report)
    print(f"\nKaydedilen modeller: {result['saved_paths']}")
