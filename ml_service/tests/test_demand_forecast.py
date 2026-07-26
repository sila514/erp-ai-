"""Talep tahmini için saf fonksiyon testleri — DB gerektirmez, sentetik veriyle."""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.demand_forecast.baselines import (
    moving_average_forecast,
    naive_forecast,
    seasonal_naive_forecast,
)
from app.demand_forecast.evaluation import expanding_window_cv, mae, mape, rmse
from app.demand_forecast.features import FEATURE_COLUMNS, calendar_features_for_date


class TestBaselines:
    def test_naive_returns_last_value(self):
        assert naive_forecast(np.array([1, 2, 3, 10])) == 10

    def test_seasonal_naive_returns_value_from_one_season_ago(self):
        # history[-season_length] semantiği: 8 elemanlı dizide season_length=7 ->
        # index -7 = index 1 (20), index 0 (10) değil.
        history = np.array([10, 20, 30, 40, 50, 60, 70, 999])
        assert seasonal_naive_forecast(history, season_length=7) == 20

    def test_seasonal_naive_falls_back_to_naive_when_insufficient_history(self):
        history = np.array([1, 2, 3])
        assert seasonal_naive_forecast(history, season_length=7) == naive_forecast(history)

    def test_moving_average_uses_available_window(self):
        history = np.array([2, 4, 6])
        assert moving_average_forecast(history, window=7) == pytest.approx(4.0)


class TestMetrics:
    def test_mae_zero_for_perfect_prediction(self):
        assert mae([1, 2, 3], [1, 2, 3]) == 0.0

    def test_rmse_penalizes_large_errors_more_than_mae(self):
        y_true = [0, 0, 0, 0]
        y_pred = [0, 0, 0, 4]
        assert rmse(y_true, y_pred) > mae(y_true, y_pred)

    def test_mape_uses_epsilon_floor_to_avoid_explosion_near_zero(self):
        # y_true=0 olduğunda eps tabanı sayesinde sonsuz/aşırı büyük değer üretmemeli
        result = mape([0], [5], eps=1.0)
        assert result == pytest.approx(500.0)


class TestCalendarFeaturesBugFix:
    """predict.py'deki eski `day_of_week=0`/`day_of_month=1` hardcoded bug'ının
    düzeltildiğini doğrular: gerçek tarihlerden hesaplanan feature'lar günden
    güne değişmeli, sabit kalmamalı."""

    def test_day_of_week_varies_across_consecutive_dates(self):
        days = [calendar_features_for_date(date(2026, 1, d))["day_of_week"] for d in range(1, 8)]
        assert len(set(days)) == 7  # bir hafta boyunca 7 farklı gün değeri olmalı

    def test_day_of_month_matches_actual_date(self):
        feats = calendar_features_for_date(date(2026, 3, 15))
        assert feats["day_of_month"] == 15
        assert feats["month"] == 3

    def test_is_weekend_true_for_saturday_and_sunday(self):
        saturday = calendar_features_for_date(date(2026, 1, 3))
        sunday = calendar_features_for_date(date(2026, 1, 4))
        monday = calendar_features_for_date(date(2026, 1, 5))
        assert saturday["is_weekend"] == 1
        assert sunday["is_weekend"] == 1
        assert monday["is_weekend"] == 0


class TestExpandingWindowCV:
    def _synthetic_features_df(self, n: int = 200) -> pd.DataFrame:
        rng = np.random.default_rng(0)
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        qty = np.maximum(0, 10 + 3 * np.sin(np.arange(n) / 7 * 2 * np.pi) + rng.normal(0, 1, n))
        df = pd.DataFrame({"day": dates, "qty": qty})
        for col in FEATURE_COLUMNS:
            df[col] = rng.normal(0, 1, n)
        # Gerçekçi olması için lag_1'i qty ile ilişkilendir (modelin öğrenebileceği sinyal olsun)
        df["lag_1"] = df["qty"].shift(1).fillna(df["qty"].mean())
        return df

    def test_returns_metrics_for_all_baselines_and_xgboost(self):
        df = self._synthetic_features_df()
        result = expanding_window_cv(df, n_splits=3, test_size=20, min_train_size=60)
        assert "xgboost" in result["summary"]
        assert "naive" in result["summary"]
        assert "seasonal_naive" in result["summary"]
        assert all(result["summary"][name]["mae"] >= 0 for name in result["summary"])

    def test_raises_when_insufficient_data(self):
        df = self._synthetic_features_df(n=50)
        with pytest.raises(ValueError):
            expanding_window_cv(df, n_splits=3, test_size=20, min_train_size=60)
