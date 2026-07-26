"""
TR resmi tatil takvimi + haftasonu yardımcı fonksiyonları.

Not: `backend/app/seed_data/calendar_effects.py` ile aynı tatil listesini
tutar. İki ayrı servis/dağıtım birimi (backend ve ml_service) oldukları için
kod paylaşımı yerine aynı mantık bilinçli olarak iki yerde bağımsız tutuluyor;
sentetik veri üretiminde kullanılan tatil takvimiyle talep tahmini
feature'larının kullandığı takvim aynı tarihleri işaret etmeli.
"""
import math
from datetime import date

FIXED_HOLIDAYS_MD = [
    (1, 1),
    (4, 23),
    (5, 1),
    (5, 19),
    (7, 15),
    (8, 30),
    (10, 29),
]

RELIGIOUS_HOLIDAYS: dict[int, list[date]] = {
    2024: [
        date(2024, 4, 10), date(2024, 4, 11), date(2024, 4, 12),
        date(2024, 6, 16), date(2024, 6, 17), date(2024, 6, 18), date(2024, 6, 19),
    ],
    2025: [
        date(2025, 3, 30), date(2025, 3, 31), date(2025, 4, 1),
        date(2025, 6, 6), date(2025, 6, 7), date(2025, 6, 8), date(2025, 6, 9),
    ],
    2026: [
        date(2026, 3, 20), date(2026, 3, 21), date(2026, 3, 22),
        date(2026, 5, 26), date(2026, 5, 27), date(2026, 5, 28), date(2026, 5, 29),
    ],
}


def is_holiday(d: date) -> bool:
    if (d.month, d.day) in FIXED_HOLIDAYS_MD:
        return True
    return d in RELIGIOUS_HOLIDAYS.get(d.year, [])


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def cyclical_day_of_year(d: date) -> tuple[float, float]:
    """Yıl içi döngüsellik için sin/cos kodlaması (31 Aralık -> 1 Ocak sıçramasını önler)."""
    frac = d.timetuple().tm_yday / 365.25
    return math.sin(2 * math.pi * frac), math.cos(2 * math.pi * frac)
