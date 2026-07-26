"""
Churn modelini sıfırdan eğitir: RFM + davranışsal feature engineering, XGBoost +
LogisticRegression baseline karşılaştırması, stratified k-fold CV, kalibrasyon
eğrisi, F1-maksimize eden eşik optimizasyonu. Üretim modeli tüm veriyle
yeniden eğitilir ve diske kaydedilir; SHAP açıklaması inference zamanında
(service.py) kayıtlı modelden üretilir.

--report bayrağıyla model_cards/churn.md yazılır.
"""
import os
from datetime import datetime, timedelta, timezone

import joblib
import mlflow
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from app.churn.feature_engineering import FEATURE_COLUMNS, build_customer_features, label_churn
from app.common.database import SessionLocal, settings
from app.common.mlflow_utils import configure_mlflow

SNAPSHOT_LAG_DAYS = 120
LABEL_HORIZON_DAYS = 90
N_FOLDS = 5

MODEL_CARD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "model_cards", "churn.md"
)


def _model_path() -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, "churn_model.joblib")


def _threshold_path() -> str:
    return os.path.join(settings.MODEL_REGISTRY_PATH, "churn_threshold.joblib")


def _prepare_dataset():
    db = SessionLocal()
    try:
        snapshot_date = datetime.now(timezone.utc) - timedelta(days=SNAPSHOT_LAG_DAYS)
        features_df = build_customer_features(db, snapshot_date)
        labels_df = label_churn(db, snapshot_date, LABEL_HORIZON_DAYS)
    finally:
        db.close()
    return features_df.merge(labels_df, on="customer_id", how="inner"), snapshot_date


def _fold_metrics(y_test, y_prob, threshold: float = 0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    auc = roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else float("nan")
    return {
        "auc_roc": auc,
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
    }


def _optimal_threshold(y_true, y_prob) -> tuple[float, dict]:
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    f1 = 2 * precision * recall / np.clip(precision + recall, 1e-9, None)
    if len(thresholds) == 0:
        return 0.5, {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    best_idx = int(np.argmax(f1[:-1]))
    return float(thresholds[best_idx]), {
        "precision": float(precision[best_idx]),
        "recall": float(recall[best_idx]),
        "f1": float(f1[best_idx]),
    }


def train_churn_model(report: bool = False) -> dict:
    df, snapshot_date = _prepare_dataset()
    if len(df) < 30 or df["churn"].nunique() < 2:
        raise ValueError("Eğitim için yetersiz veri veya tek sınıflı etiket dağılımı")

    X = df[FEATURE_COLUMNS].values.astype(float)
    y = df["churn"].values.astype(int)

    n_splits = min(N_FOLDS, int(np.bincount(y).min()))
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    fold_metrics = {"xgboost": [], "logistic_regression": []}
    oof_xgb_prob = np.zeros(len(y))

    for train_idx, test_idx in skf.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        xgb = XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, eval_metric="logloss", random_state=42,
        )
        xgb.fit(X_train, y_train)
        xgb_prob = xgb.predict_proba(X_test)[:, 1]
        oof_xgb_prob[test_idx] = xgb_prob
        fold_metrics["xgboost"].append(_fold_metrics(y_test, xgb_prob))

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        lr = LogisticRegression(max_iter=1000, class_weight="balanced")
        lr.fit(X_train_s, y_train)
        lr_prob = lr.predict_proba(X_test_s)[:, 1]
        fold_metrics["logistic_regression"].append(_fold_metrics(y_test, lr_prob))

    summary = {
        name: {
            "auc_roc": float(np.nanmean([m["auc_roc"] for m in folds])),
            "precision@0.5": float(np.mean([m["precision"] for m in folds])),
            "recall@0.5": float(np.mean([m["recall"] for m in folds])),
        }
        for name, folds in fold_metrics.items()
    }

    threshold, threshold_metrics = _optimal_threshold(y, oof_xgb_prob)
    calib_true, calib_pred = calibration_curve(y, oof_xgb_prob, n_bins=min(5, n_splits), strategy="quantile")

    # Üretim modeli: tüm veriyle yeniden eğitilir (CV yalnızca dürüst değerlendirme amaçlı)
    final_model = XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric="logloss", random_state=42,
    )
    final_model.fit(X, y)

    os.makedirs(settings.MODEL_REGISTRY_PATH, exist_ok=True)
    joblib.dump(final_model, _model_path())
    joblib.dump(threshold, _threshold_path())

    result = {
        "n_samples": len(df),
        "churn_rate": float(y.mean()),
        "cv_summary": summary,
        "optimal_threshold": threshold,
        "threshold_metrics": threshold_metrics,
        "calibration": {"true": calib_true.tolist(), "pred": calib_pred.tolist()},
        "n_folds": n_splits,
    }

    if report:
        print(
            f"\n=== Churn modeli — {n_splits}-fold stratified CV (n={len(df)}, "
            f"churn_rate={y.mean():.1%}) ==="
        )
        print(f"{'Model':<22}{'AUC-ROC':>10}{'Precision@0.5':>16}{'Recall@0.5':>13}")
        for name, m in summary.items():
            print(f"{name:<22}{m['auc_roc']:>10.3f}{m['precision@0.5']:>16.3f}{m['recall@0.5']:>13.3f}")
        print(
            f"\nF1-optimal eşik: {threshold:.3f} "
            f"(precision={threshold_metrics['precision']:.3f}, "
            f"recall={threshold_metrics['recall']:.3f}, f1={threshold_metrics['f1']:.3f})"
        )
        print(
            "Kalibrasyon (gözlenen vs tahmin, quantile bin): "
            f"{list(zip([round(v, 3) for v in calib_true], [round(v, 3) for v in calib_pred]))}"
        )
        _log_to_mlflow(result)
        _write_model_card(result, snapshot_date)

    return result


def _log_to_mlflow(result: dict) -> None:
    configure_mlflow("churn")
    with mlflow.start_run(run_name=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")):
        mlflow.log_params(
            {"n_samples": result["n_samples"], "n_folds": result["n_folds"], "snapshot_lag_days": SNAPSHOT_LAG_DAYS}
        )
        for model_name, metrics in result["cv_summary"].items():
            for metric_name, value in metrics.items():
                safe_name = metric_name.replace("@", "_at_")
                mlflow.log_metric(f"{model_name}_{safe_name}", value)
        mlflow.log_metric("churn_rate", result["churn_rate"])
        mlflow.log_metric("optimal_threshold", result["optimal_threshold"])
        mlflow.log_metrics({f"threshold_{k}": v for k, v in result["threshold_metrics"].items()})


def _write_model_card(result: dict, snapshot_date) -> None:
    os.makedirs(os.path.dirname(MODEL_CARD_PATH), exist_ok=True)
    summary = result["cv_summary"]
    lines = [
        "# Model Card — Müşteri Churn Tahmini",
        "",
        f"**Son güncelleme**: {datetime.now(timezone.utc).isoformat()}",
        f"**Eğitim snapshot tarihi**: {snapshot_date.isoformat()} (bugünden {SNAPSHOT_LAG_DAYS} gün önce)",
        "",
        "## Veri",
        f"- Örneklem: {result['n_samples']} müşteri, churn oranı %{result['churn_rate'] * 100:.1f}",
        f"- Etiket: snapshot tarihinden sonraki {LABEL_HORIZON_DAYS} gün içinde satın alma yoksa churn=1 "
        "(leakage'siz — feature'lar sadece snapshot'tan önceki veriyi kullanır).",
        f"- Feature'lar: {', '.join(FEATURE_COLUMNS)}",
        "",
        "## Yöntem",
        f"- {result['n_folds']}-fold stratified cross-validation ile XGBoost ve LogisticRegression "
        "(baseline) karşılaştırıldı; üretim modeli tüm veriyle yeniden eğitildi.",
        "- SHAP (TreeExplainer) ile birey bazlı açıklama; API yanıtındaki `top_factors` gerçek SHAP "
        "değerlerinden üretilir (bkz. `service.py`).",
        "- Eşik: out-of-fold tahminlerden precision-recall eğrisi ile F1-maksimize eden nokta seçildi "
        "(gerçek bir iş maliyet matrisi olmadığından bu başlangıç noktasıdır).",
        "",
        "## Sonuçlar (CV ortalaması, out-of-fold)",
        "",
        "| Model | AUC-ROC | Precision@0.5 | Recall@0.5 |",
        "|---|---|---|---|",
    ]
    for name, m in summary.items():
        lines.append(f"| {name} | {m['auc_roc']:.3f} | {m['precision@0.5']:.3f} | {m['recall@0.5']:.3f} |")

    lines += [
        "",
        f"**F1-optimal eşik**: {result['optimal_threshold']:.3f} "
        f"(precision={result['threshold_metrics']['precision']:.3f}, "
        f"recall={result['threshold_metrics']['recall']:.3f}, "
        f"f1={result['threshold_metrics']['f1']:.3f})",
        "",
        "## Kalibrasyon",
        "Gözlenen vs tahmin edilen olasılık (quantile bin): "
        f"{list(zip([round(v, 3) for v in result['calibration']['true']], [round(v, 3) for v in result['calibration']['pred']]))}",
        "",
        "## Sınırlılıklar",
        "- Eşik F1-optimal seçildi; gerçek iş maliyeti (yanlış pozitif/negatif maliyeti) girilirse değişmeli.",
        "- Örneklem boyutu (~birkaç yüz müşteri) SHAP/kalibrasyon gibi tekniklerin güvenilirliğini sınırlar; "
        "üretimde müşteri sayısı arttıkça yeniden değerlendirilmeli.",
        "- `anomaly_ratio` feature'ı şu an çoğunlukla sıfır (anomali işaretleme canlı olay akışıyla "
        "oluşur, sentetik veri seed'inde önceden etiketlenmez).",
        "",
    ]
    with open(MODEL_CARD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    import sys

    train_churn_model(report="--report" in sys.argv)
