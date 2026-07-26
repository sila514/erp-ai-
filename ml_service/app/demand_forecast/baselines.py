"""
Talep tahmini için basit baseline'lar. XGBoost modelinin bu baseline'ları
gerçekten geçtiğini kanıtlamak `evaluation.py`'nin işi; burada sadece
tek-adım-ileri tahmin üreten saf fonksiyonlar var (DB gerektirmez, test edilebilir).
"""
import numpy as np


def naive_forecast(history: np.ndarray) -> float:
    """Son gözlenen değeri döndürür."""
    return float(history[-1])


def seasonal_naive_forecast(history: np.ndarray, season_length: int = 7) -> float:
    """`season_length` gün önceki değeri döndürür (yeterli geçmiş yoksa naive'e düşer)."""
    if len(history) < season_length:
        return naive_forecast(history)
    return float(history[-season_length])


def moving_average_forecast(history: np.ndarray, window: int = 7) -> float:
    """Son `window` günün ortalamasını döndürür."""
    w = min(window, len(history))
    return float(np.mean(history[-w:]))


BASELINES = {
    "naive": naive_forecast,
    "seasonal_naive": seasonal_naive_forecast,
    "moving_average_7": moving_average_forecast,
}
