"""
Korelasyon ve istatistiksel anlamlılık analizi — saf fonksiyonlar (DB
gerektirmez, doğrudan pandas/numpy girdileriyle çalışır). Veri yükleme
`ml_service/app/analytics/router.py`'de yapılır.

ÖNEMLİ: Bu modüldeki hiçbir fonksiyon nedensellik iddiası yapmaz — sadece
istatistiksel ilişki (korelasyon, birliktelik) ölçer. "Korelasyon nedensellik
değildir" uyarısı API yanıtlarına ve frontend'e taşınır.
"""
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, f_oneway, pearsonr, pointbiserialr, spearmanr
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant
from statsmodels.tsa.stattools import acf, adfuller, pacf

DEFAULT_CORRECTION_METHOD = "fdr_bh"  # Benjamini-Hochberg — exploratory korelasyon taraması için standart


def _sanitize(value):
    """NaN/Infinity JSON-uyumlu değildir; API yanıtlarına geçmeden None'a çevrilir."""
    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
        return None
    return value


def _sanitize_matrix(matrix: list[list[float]]) -> list[list[float | None]]:
    return [[_sanitize(v) for v in row] for row in matrix]


def correlation_matrix(df: pd.DataFrame, correction_method: str = DEFAULT_CORRECTION_METHOD) -> dict:
    """Sayısal kolonlar için Pearson + Spearman korelasyon matrisi — ikisi birlikte
    (Spearman, Pearson'ın kaçırdığı lineer olmayan monotonik ilişkileri yakalar).
    Her hücre için p-value + çoklu test düzeltmesi (varsayılan FDR/Benjamini-Hochberg
    — çok sayıda çift test edildiğinde bazılarının şans eseri anlamlı çıkmasını önler)."""
    numeric_df = df.select_dtypes(include=[np.number]).dropna(axis=1, how="all")
    numeric_df = numeric_df.loc[:, numeric_df.nunique(dropna=True) > 1]
    cols = numeric_df.columns.tolist()
    n = len(cols)

    pearson_r = [[1.0 if i == j else np.nan for j in range(n)] for i in range(n)]
    spearman_r = [[1.0 if i == j else np.nan for j in range(n)] for i in range(n)]
    pearson_p = [[np.nan] * n for _ in range(n)]
    spearman_p = [[np.nan] * n for _ in range(n)]

    pair_index = []
    raw_p_pearson = []
    raw_p_spearman = []

    for i in range(n):
        for j in range(i + 1, n):
            xi = numeric_df.iloc[:, i]
            xj = numeric_df.iloc[:, j]
            valid = xi.notna() & xj.notna()
            if valid.sum() < 3:
                continue
            r_p, p_p = pearsonr(xi[valid], xj[valid])
            r_s, p_s = spearmanr(xi[valid], xj[valid])
            pearson_r[i][j] = pearson_r[j][i] = float(r_p)
            spearman_r[i][j] = spearman_r[j][i] = float(r_s)
            pearson_p[i][j] = pearson_p[j][i] = float(p_p)
            spearman_p[i][j] = spearman_p[j][i] = float(p_s)
            pair_index.append((i, j))
            raw_p_pearson.append(p_p)
            raw_p_spearman.append(p_s)

    pearson_p_corrected = [[np.nan] * n for _ in range(n)]
    spearman_p_corrected = [[np.nan] * n for _ in range(n)]
    if pair_index:
        _, corrected_pearson, _, _ = multipletests(raw_p_pearson, method=correction_method)
        _, corrected_spearman, _, _ = multipletests(raw_p_spearman, method=correction_method)
        for (i, j), cp, cs in zip(pair_index, corrected_pearson, corrected_spearman):
            pearson_p_corrected[i][j] = pearson_p_corrected[j][i] = float(cp)
            spearman_p_corrected[i][j] = spearman_p_corrected[j][i] = float(cs)

    return {
        "columns": cols,
        "pearson_r": _sanitize_matrix(pearson_r),
        "pearson_p": _sanitize_matrix(pearson_p),
        "pearson_p_corrected": _sanitize_matrix(pearson_p_corrected),
        "spearman_r": _sanitize_matrix(spearman_r),
        "spearman_p": _sanitize_matrix(spearman_p),
        "spearman_p_corrected": _sanitize_matrix(spearman_p_corrected),
        "correction_method": correction_method,
        "n_observations": int(len(numeric_df)),
        "n_pairs_tested": len(pair_index),
    }


def acf_pacf_analysis(series: np.ndarray, max_lag: int = 30) -> dict:
    """ACF/PACF (lag feature seçimini gerekçelendirmek için) + ADF stationarity testi
    (korelasyona bakmadan önce trend'i tespit etmek için) + differencing sonrası
    ADF (spurious correlation'ı önlemek için: trend'li iki seri, aralarında gerçek
    bir ilişki olmasa bile yüksek korelasyon gösterebilir — differencing bunu ayıklar)."""
    series = np.asarray(series, dtype=float)
    max_lag = min(max_lag, len(series) // 2 - 1)

    acf_vals = acf(series, nlags=max_lag, fft=True)
    pacf_vals = pacf(series, nlags=max_lag, method="ywm")

    adf_stat, adf_p, *_ = adfuller(series)
    differenced = np.diff(series)
    adf_stat_diff, adf_p_diff, *_ = adfuller(differenced)

    return {
        "lags": list(range(max_lag + 1)),
        "acf": [float(v) for v in acf_vals],
        "pacf": [float(v) for v in pacf_vals],
        "adf_test": {
            "statistic": float(adf_stat),
            "p_value": float(adf_p),
            "is_stationary": bool(adf_p < 0.05),
        },
        "differenced_adf_test": {
            "statistic": float(adf_stat_diff),
            "p_value": float(adf_p_diff),
            "is_stationary": bool(adf_p_diff < 0.05),
        },
    }


def cross_correlation(series_a: np.ndarray, series_b: np.ndarray, max_lag: int = 14) -> dict:
    """İki seri arasında lag'li ilişki. Pozitif lag: `series_a`, `series_b`'den
    `lag` gün önce gerçekleşiyor (örn. lag=5 -> kampanya harcaması satıştan 5 gün
    önce). En güçlü mutlak korelasyonun olduğu lag `best_lag` olarak döner."""
    a = np.asarray(series_a, dtype=float)
    b = np.asarray(series_b, dtype=float)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]

    results = []
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a[: n - lag], b[lag:]
        else:
            x, y = a[-lag:], b[: n + lag]
        if len(x) < 10 or np.std(x) == 0 or np.std(y) == 0:
            continue
        r, p = pearsonr(x, y)
        results.append({"lag": lag, "correlation": float(r), "p_value": float(p)})

    best = max(results, key=lambda item: abs(item["correlation"])) if results else None
    return {"results": results, "best_lag": best}


def variance_inflation_factors(df: pd.DataFrame, vif_threshold: float = 10.0) -> dict:
    """VIF (Variance Inflation Factor) — multicollinearity tespiti. VIF > 10 olan
    feature'lar raporlanır ve modelden çıkarılması/birleştirilmesi önerilir."""
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    numeric_df = numeric_df.loc[:, numeric_df.std(numeric_only=True) > 1e-9]
    if numeric_df.shape[1] < 2:
        return {"vif_threshold": vif_threshold, "results": []}

    X = add_constant(numeric_df, has_constant="add")
    feature_cols = [c for c in X.columns if c != "const"]

    results = []
    for col in feature_cols:
        idx = X.columns.get_loc(col)
        try:
            vif_value = float(variance_inflation_factor(X.values, idx))
            if np.isinf(vif_value) or np.isnan(vif_value):
                vif_value = None
        except (ZeroDivisionError, np.linalg.LinAlgError):
            vif_value = None
        results.append(
            {
                "feature": col,
                "vif": vif_value,
                "high_multicollinearity": bool(vif_value is not None and vif_value > vif_threshold),
            }
        )

    results.sort(key=lambda item: item["vif"] if item["vif"] is not None else float("inf"), reverse=True)
    high_vif_features = [r["feature"] for r in results if r["high_multicollinearity"]]
    recommendation = (
        f"VIF>{vif_threshold} olan feature'lar ({', '.join(high_vif_features)}) yüksek "
        "çoklu doğrusal bağlantı gösteriyor — birini çıkarmak veya PCA/birleştirme "
        "uygulamak önerilir."
        if high_vif_features
        else "Belirgin bir multicollinearity tespit edilmedi."
    )
    return {"vif_threshold": vif_threshold, "results": results, "recommendation": recommendation}


def cramers_v(x: pd.Series, y: pd.Series) -> dict:
    """İki kategorik değişken arasındaki ilişki — bias-corrected Cramér's V
    (Bergsma 2013 düzeltmesi, küçük örneklemlerde şişkinliği azaltır)."""
    contingency = pd.crosstab(x, y)
    chi2, p, _, _ = chi2_contingency(contingency)
    n = contingency.sum().sum()
    r, k = contingency.shape
    phi2 = chi2 / n
    phi2_corrected = max(0.0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    r_corrected = r - ((r - 1) ** 2) / (n - 1)
    k_corrected = k - ((k - 1) ** 2) / (n - 1)
    denom = min(k_corrected - 1, r_corrected - 1)
    v = float(np.sqrt(phi2_corrected / denom)) if denom > 0 else 0.0
    return {"cramers_v": v, "p_value": float(p), "chi2": float(chi2)}


def point_biserial(binary: pd.Series, continuous: pd.Series) -> dict:
    """İkili (0/1) bir değişken ile sürekli bir değişken arasındaki ilişki."""
    r, p = pointbiserialr(binary, continuous)
    return {"correlation": float(r), "p_value": float(p)}


def anova_f_test(categorical: pd.Series, numeric: pd.Series) -> dict:
    """Kategori grupları arasında sayısal hedefin ortalaması anlamlı farklı mı
    (tek yönlü ANOVA F-testi) — kategori ↔ sayısal hedef ilişkisi için."""
    groups = [group.values for _, group in numeric.groupby(categorical) if len(group) > 1]
    if len(groups) < 2:
        return {"f_statistic": None, "p_value": None}
    f_stat, p = f_oneway(*groups)
    return {"f_statistic": float(f_stat), "p_value": float(p)}


def feature_target_importance(
    X: pd.DataFrame,
    y: pd.Series,
    task: str = "regression",
    correction_method: str = DEFAULT_CORRECTION_METHOD,
) -> dict:
    """Her feature için Pearson korelasyonu + p-value + mutual information —
    birlikte tek bir tabloda (korelasyon lineer ilişkiyi, mutual information
    lineer olmayan bağımlılıkları da yakalar). `task='classification'` ise
    mutual_info_classif, aksi halde mutual_info_regression kullanılır.
    Çoklu test düzeltmesi (varsayılan FDR) p-value'lara uygulanır."""
    mi_func = mutual_info_classif if task == "classification" else mutual_info_regression
    mi_scores = mi_func(X, y, random_state=42)

    rows = []
    testable_indices = []
    raw_p = []
    for i, col in enumerate(X.columns):
        if X[col].nunique() < 2:
            # Sabit feature: korelasyon tanımsız (varyans yok) — mutual information zaten ~0 olur
            rows.append(
                {
                    "feature": col,
                    "correlation": None,
                    "p_value": None,
                    "mutual_information": float(mi_scores[i]),
                    "p_value_corrected": None,
                    "significant": False,
                }
            )
            continue
        r, p = pearsonr(X[col], y)
        rows.append(
            {
                "feature": col,
                "correlation": _sanitize(float(r)),
                "p_value": _sanitize(float(p)),
                "mutual_information": float(mi_scores[i]),
            }
        )
        testable_indices.append(len(rows) - 1)
        raw_p.append(p)

    if raw_p:
        _, corrected_p, _, _ = multipletests(raw_p, method=correction_method)
        for row_idx, cp in zip(testable_indices, corrected_p):
            rows[row_idx]["p_value_corrected"] = _sanitize(float(cp))
            rows[row_idx]["significant"] = bool(cp < 0.05)

    rows.sort(key=lambda item: abs(item["mutual_information"]), reverse=True)
    return {"correction_method": correction_method, "results": rows}
