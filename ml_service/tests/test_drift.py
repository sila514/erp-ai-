"""Veri drift (PSI/KS) için saf fonksiyon testleri — DB gerektirmez."""
import numpy as np

from app.monitoring.drift import (
    PSI_SIGNIFICANT_THRESHOLD,
    interpret_psi,
    ks_drift_test,
    population_stability_index,
)


class TestPSI:
    def test_identical_distributions_have_near_zero_psi(self):
        rng = np.random.default_rng(0)
        data = rng.normal(0, 1, 1000)
        psi = population_stability_index(data, data.copy())
        assert psi < 0.01

    def test_shifted_distribution_has_significant_psi(self):
        rng = np.random.default_rng(0)
        expected = rng.normal(0, 1, 1000)
        actual = rng.normal(5, 1, 1000)  # belirgin ortalama kayması
        psi = population_stability_index(expected, actual)
        assert psi > PSI_SIGNIFICANT_THRESHOLD

    def test_empty_input_returns_zero(self):
        assert population_stability_index(np.array([]), np.array([1, 2, 3])) == 0.0


class TestInterpretPSI:
    def test_thresholds(self):
        assert interpret_psi(0.05) == "önemli değişim yok"
        assert interpret_psi(0.15) == "orta düzey drift"
        assert interpret_psi(0.30) == "önemli drift"


class TestKSDriftTest:
    def test_same_distribution_not_flagged_as_drifted(self):
        rng = np.random.default_rng(0)
        expected = rng.normal(0, 1, 500)
        actual = rng.normal(0, 1, 500)
        result = ks_drift_test(expected, actual)
        assert result["drifted"] is False

    def test_clearly_different_distribution_flagged_as_drifted(self):
        rng = np.random.default_rng(0)
        expected = rng.normal(0, 1, 500)
        actual = rng.uniform(10, 20, 500)
        result = ks_drift_test(expected, actual)
        assert result["drifted"] is True
        assert result["p_value"] < 0.05
