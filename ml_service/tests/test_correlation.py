"""Korelasyon/istatistik modülü için saf fonksiyon testleri — DB gerektirmez, sentetik veriyle."""
import numpy as np
import pandas as pd
import pytest

from app.analytics.correlation import (
    acf_pacf_analysis,
    anova_f_test,
    correlation_matrix,
    cramers_v,
    cross_correlation,
    feature_target_importance,
    point_biserial,
    variance_inflation_factors,
)


class TestCorrelationMatrix:
    def test_diagonal_is_one(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({"a": rng.normal(size=100), "b": rng.normal(size=100)})
        result = correlation_matrix(df)
        assert result["pearson_r"][0][0] == 1.0
        assert result["pearson_r"][1][1] == 1.0

    def test_perfectly_correlated_columns_have_r_near_one(self):
        rng = np.random.default_rng(0)
        x = rng.normal(size=200)
        df = pd.DataFrame({"x": x, "y": x * 2 + 1})
        result = correlation_matrix(df)
        i, j = result["columns"].index("x"), result["columns"].index("y")
        assert result["pearson_r"][i][j] == pytest.approx(1.0, abs=1e-6)

    def test_returns_none_not_nan_for_json_safety(self):
        # sabit bir kolon (varyans yok) -> korelasyon tanımsız, None dönmeli (NaN değil)
        df = pd.DataFrame({"constant": [5] * 50, "varying": np.arange(50)})
        result = correlation_matrix(df)
        # sabit kolon nunique<=1 olduğu için tamamen filtrelenir
        assert "constant" not in result["columns"]

    def test_multiple_testing_correction_is_at_least_as_conservative_as_raw_p(self):
        rng = np.random.default_rng(1)
        df = pd.DataFrame({f"col_{i}": rng.normal(size=50) for i in range(6)})
        result = correlation_matrix(df, correction_method="fdr_bh")
        for i in range(len(result["columns"])):
            for j in range(len(result["columns"])):
                raw = result["pearson_p"][i][j]
                corrected = result["pearson_p_corrected"][i][j]
                if raw is not None and corrected is not None:
                    assert corrected >= raw - 1e-9


class TestACFPACF:
    def test_weekly_seasonality_produces_spike_at_lag_7(self):
        t = np.arange(200)
        series = 10 + 5 * np.sin(2 * np.pi * t / 7) + np.random.default_rng(0).normal(0, 0.1, 200)
        result = acf_pacf_analysis(series, max_lag=14)
        assert result["acf"][7] > result["acf"][3]
        assert result["acf"][7] > result["acf"][10]

    def test_adf_flags_random_walk_as_non_stationary_trend_series(self):
        rng = np.random.default_rng(0)
        random_walk = np.cumsum(rng.normal(0, 1, 300))  # birim kök içeren klasik durağan olmayan seri
        result = acf_pacf_analysis(random_walk, max_lag=10)
        assert result["adf_test"]["is_stationary"] is False

    def test_differencing_a_random_walk_makes_it_stationary(self):
        rng = np.random.default_rng(0)
        random_walk = np.cumsum(rng.normal(0, 1, 300))
        result = acf_pacf_analysis(random_walk, max_lag=10)
        assert result["differenced_adf_test"]["is_stationary"] is True


class TestCrossCorrelation:
    def test_recovers_known_lag_between_two_series(self):
        rng = np.random.default_rng(0)
        n = 300
        driver = rng.normal(0, 1, n)
        # 'response', driver'dan 5 gün sonra gerçekleşiyor
        response = np.zeros(n)
        response[5:] = driver[:-5]
        response += rng.normal(0, 0.05, n)

        result = cross_correlation(driver, response, max_lag=10)
        assert result["best_lag"] is not None
        assert result["best_lag"]["lag"] == 5
        assert result["best_lag"]["correlation"] > 0.9


class TestVIF:
    def test_collinear_features_get_high_vif(self):
        rng = np.random.default_rng(0)
        x = rng.normal(size=200)
        df = pd.DataFrame({"x": x, "x_copy": x + rng.normal(0, 0.01, 200), "independent": rng.normal(size=200)})
        result = variance_inflation_factors(df)
        vif_by_feature = {r["feature"]: r["vif"] for r in result["results"]}
        assert vif_by_feature["x"] > 10
        assert vif_by_feature["x_copy"] > 10
        assert vif_by_feature["independent"] < 10

    def test_independent_features_have_low_vif(self):
        rng = np.random.default_rng(0)
        df = pd.DataFrame({f"col_{i}": rng.normal(size=200) for i in range(4)})
        result = variance_inflation_factors(df)
        assert all(not r["high_multicollinearity"] for r in result["results"])


class TestCategoricalAssociations:
    def test_cramers_v_high_for_perfectly_associated_categories(self):
        x = pd.Series(["a", "a", "b", "b"] * 20)
        y = pd.Series(["x", "x", "y", "y"] * 20)
        result = cramers_v(x, y)
        assert result["cramers_v"] == pytest.approx(1.0, abs=0.05)
        assert result["p_value"] < 0.05

    def test_cramers_v_low_for_independent_categories(self):
        rng = np.random.default_rng(0)
        x = pd.Series(rng.choice(["a", "b"], size=300))
        y = pd.Series(rng.choice(["x", "y"], size=300))
        result = cramers_v(x, y)
        assert result["cramers_v"] < 0.2

    def test_point_biserial_detects_group_mean_difference(self):
        rng = np.random.default_rng(0)
        binary = pd.Series([0] * 100 + [1] * 100)
        continuous = pd.Series(np.concatenate([rng.normal(0, 1, 100), rng.normal(5, 1, 100)]))
        result = point_biserial(binary, continuous)
        assert abs(result["correlation"]) > 0.8
        assert result["p_value"] < 0.05

    def test_anova_detects_group_mean_difference(self):
        rng = np.random.default_rng(0)
        categorical = pd.Series(["A"] * 50 + ["B"] * 50 + ["C"] * 50)
        numeric = pd.Series(
            np.concatenate([rng.normal(0, 1, 50), rng.normal(10, 1, 50), rng.normal(20, 1, 50)])
        )
        result = anova_f_test(categorical, numeric)
        assert result["p_value"] < 0.001


class TestFeatureTargetImportance:
    def test_ranks_relevant_feature_above_irrelevant_noise(self):
        rng = np.random.default_rng(0)
        n = 300
        relevant = rng.normal(size=n)
        noise = rng.normal(size=n)
        y = relevant * 3 + rng.normal(0, 0.1, n)
        X = pd.DataFrame({"relevant": relevant, "noise": noise})

        result = feature_target_importance(X, y, task="regression")
        top_feature = result["results"][0]["feature"]
        assert top_feature == "relevant"

    def test_constant_feature_is_not_significant(self):
        rng = np.random.default_rng(0)
        n = 100
        X = pd.DataFrame({"constant": [1.0] * n, "varying": rng.normal(size=n)})
        y = rng.normal(size=n)
        result = feature_target_importance(X, y, task="regression")
        constant_row = next(r for r in result["results"] if r["feature"] == "constant")
        assert constant_row["significant"] is False
        assert constant_row["correlation"] is None
