"""
Expanding-window (walk-forward) zaman serisi CV: XGBoost modelini naive,
seasonal_naive ve moving_average baseline'larıyla aynı katlarda karşılaştırır.
MAE/RMSE/MAPE hesaplar. Saf fonksiyonlar (DB gerektirmez) — pytest ile test edilir.
"""
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from app.demand_forecast.baselines import BASELINES
from app.demand_forecast.features import FEATURE_COLUMNS


def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.array(y_true, dtype=float) - np.array(y_pred, dtype=float))))


def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.array(y_true, dtype=float) - np.array(y_pred, dtype=float)) ** 2)))


def mape(y_true, y_pred, eps: float = 1.0) -> float:
    """`eps` tabanı sıfıra yakın günlerde MAPE'nin patlamasını önler (perakende talebinde sık görülür)."""
    y_true_arr = np.array(y_true, dtype=float)
    y_pred_arr = np.array(y_pred, dtype=float)
    denom = np.maximum(np.abs(y_true_arr), eps)
    return float(np.mean(np.abs(y_true_arr - y_pred_arr) / denom) * 100)


def expanding_window_cv(
    features_df: pd.DataFrame,
    n_splits: int = 5,
    test_size: int = 30,
    min_train_size: int = 60,
) -> dict:
    """
    features_df: build_features() çıktısı (kronolojik sıra, sıfırlanmış index).
    Her katlamada [0, train_end) ile eğitilir, [train_end, train_end+test_size) ile
    test edilir; train_end her katlamada ileri kayar (expanding window, walk-forward).
    """
    n = len(features_df)
    max_train_end = n - test_size
    if max_train_end <= min_train_size:
        raise ValueError("CV için yetersiz veri: daha uzun bir geçmiş gerekiyor")

    step = max(1, (max_train_end - min_train_size) // max(n_splits - 1, 1))
    train_ends = sorted(set(min(min_train_size + i * step, max_train_end) for i in range(n_splits)))

    fold_metrics = {"xgboost": [], **{name: [] for name in BASELINES}}
    fold_info = []
    full_qty = features_df["qty"].values

    for train_end in train_ends:
        train = features_df.iloc[:train_end]
        test = features_df.iloc[train_end : train_end + test_size]
        if len(test) == 0:
            continue

        X_train, y_train = train[FEATURE_COLUMNS], train["qty"]
        X_test, y_test = test[FEATURE_COLUMNS], test["qty"]

        model = XGBRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, random_state=42,
        )
        model.fit(X_train, y_train)
        xgb_preds = model.predict(X_test)
        fold_metrics["xgboost"].append(
            {"mae": mae(y_test, xgb_preds), "rmse": rmse(y_test, xgb_preds), "mape": mape(y_test, xgb_preds)}
        )

        for name, fn in BASELINES.items():
            preds = [fn(full_qty[:t]) for t in range(train_end, train_end + len(test))]
            fold_metrics[name].append(
                {"mae": mae(y_test, preds), "rmse": rmse(y_test, preds), "mape": mape(y_test, preds)}
            )

        fold_info.append({"train_end": int(train_end), "test_size": len(test)})

    summary = {}
    for name, folds in fold_metrics.items():
        if not folds:
            continue
        summary[name] = {
            "mae": float(np.mean([m["mae"] for m in folds])),
            "rmse": float(np.mean([m["rmse"] for m in folds])),
            "mape": float(np.mean([m["mape"] for m in folds])),
            "n_folds": len(folds),
        }

    baseline_maes = [summary[name]["mae"] for name in BASELINES if name in summary]
    best_baseline_mae = min(baseline_maes) if baseline_maes else None
    beats_baseline = (
        best_baseline_mae is not None
        and "xgboost" in summary
        and summary["xgboost"]["mae"] < best_baseline_mae
    )

    return {"folds": fold_info, "summary": summary, "beats_best_baseline": beats_baseline}


def format_cv_table(cv_result: dict) -> str:
    lines = [f"{'Model':<20}{'MAE':>10}{'RMSE':>10}{'MAPE %':>10}{'Fold':>8}"]
    for name, m in cv_result["summary"].items():
        lines.append(f"{name:<20}{m['mae']:>10.2f}{m['rmse']:>10.2f}{m['mape']:>10.1f}{m['n_folds']:>8}")
    lines.append(f"\nXGBoost baseline'ı geçti mi: {cv_result['beats_best_baseline']}")
    return "\n".join(lines)
