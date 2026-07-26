"""
Veri drift kontrolü: PSI (Population Stability Index) ve KS (Kolmogorov-Smirnov)
testi. Yeniden eğitim öncesi yeni verinin dağılımını, önceki eğitimin referans
dağılımıyla karşılaştırmak için kullanılır — saf fonksiyonlar, DB gerektirmez.
"""
import numpy as np
from scipy.stats import ks_2samp

# Yaygın kabul gören PSI eşikleri (kredi skorlama / MLOps pratiğinde standart)
PSI_MODERATE_THRESHOLD = 0.1
PSI_SIGNIFICANT_THRESHOLD = 0.25


def population_stability_index(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """PSI < 0.1: önemli değişim yok, 0.1-0.25: orta düzey, > 0.25: önemli drift.
    `expected`: referans (eski) dağılım, `actual`: yeni dağılım."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    breakpoints = np.quantile(expected, np.linspace(0, 1, buckets + 1))
    breakpoints[0] -= 1e-6
    breakpoints[-1] += 1e-6
    breakpoints = np.unique(breakpoints)
    if len(breakpoints) < 3:
        return 0.0

    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)

    expected_pct = np.clip(expected_counts / max(len(expected), 1), 1e-4, None)
    actual_pct = np.clip(actual_counts / max(len(actual), 1), 1e-4, None)

    return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))


def interpret_psi(psi: float) -> str:
    if psi < PSI_MODERATE_THRESHOLD:
        return "önemli değişim yok"
    if psi < PSI_SIGNIFICANT_THRESHOLD:
        return "orta düzey drift"
    return "önemli drift"


def ks_drift_test(expected: np.ndarray, actual: np.ndarray, alpha: float = 0.05) -> dict:
    """İki bağımsız örneklemin aynı dağılımdan gelip gelmediğini test eder
    (iki-örnekli KS testi). `drifted=True` ise p_value < alpha, yani dağılımların
    farklı olduğu istatistiksel olarak anlamlı."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    statistic, p_value = ks_2samp(expected, actual)
    return {"statistic": float(statistic), "p_value": float(p_value), "drifted": bool(p_value < alpha)}
