"""
Takvim etkileri: TR resmi tatilleri + haftalık/yıllık mevsimsellik eğrileri +
şirket geneli kampanya takvimi.

Bu modül `backend/app/seed.py` tarafından sentetik veri üretirken kullanılır.
ml_service tarafı aynı tatil listesini `app/common/calendar.py` içinde bağımsız
olarak tutar (iki ayrı servis/dağıtım birimi olduğu için kod paylaşımı yerine
aynı mantık kasıtlı olarak iki yerde tutuluyor) — talep tahmini feature'ları
(`is_holiday`, `is_weekend`) buradaki ile aynı tarihleri kullanmalı.
"""
import math
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

FIXED_HOLIDAYS_MD = [
    (1, 1),    # Yılbaşı
    (4, 23),   # Ulusal Egemenlik ve Çocuk Bayramı
    (5, 1),    # Emek ve Dayanışma Günü
    (5, 19),   # Atatürk'ü Anma Gençlik ve Spor Bayramı
    (7, 15),   # Demokrasi ve Millî Birlik Günü
    (8, 30),   # Zafer Bayramı
    (10, 29),  # Cumhuriyet Bayramı
]

# Dini bayramlar yıldan yıla kayar; 2024-2026 için yaklaşık tarihler sabit olarak listelenir.
RELIGIOUS_HOLIDAYS: dict[int, list[date]] = {
    2024: [
        date(2024, 4, 10), date(2024, 4, 11), date(2024, 4, 12),  # Ramazan Bayramı
        date(2024, 6, 16), date(2024, 6, 17), date(2024, 6, 18), date(2024, 6, 19),  # Kurban Bayramı
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

WEEKLY_MULTIPLIER = {
    0: 1.05,  # Pazartesi
    1: 1.00,
    2: 1.00,
    3: 1.05,
    4: 1.15,  # Cuma
    5: 0.75,  # Cumartesi
    6: 0.55,  # Pazar
}


def is_holiday(d: date) -> bool:
    if (d.month, d.day) in FIXED_HOLIDAYS_MD:
        return True
    return d in RELIGIOUS_HOLIDAYS.get(d.year, [])


def holiday_multiplier(d: date) -> float:
    """Tatil günü talebi düşer; tatil öncesi 1-2 gün hazırlık alışverişiyle hafif yükselir."""
    if is_holiday(d):
        return 0.35
    for delta in (1, 2):
        if is_holiday(d + timedelta(days=delta)):
            return 1.25
    return 1.0


def weekly_multiplier(d: date) -> float:
    return WEEKLY_MULTIPLIER[d.weekday()]


def annual_multiplier(d: date, amplitude: float = 0.25, phase_month: float = 7.0) -> float:
    """Yıl içi mevsimsellik: `phase_month`'ta zirve yapan bir sinüs eğrisi."""
    day_of_year_frac = d.timetuple().tm_yday / 365.25
    phase_frac = (phase_month - 1) / 12
    return 1.0 + amplitude * math.sin(2 * math.pi * (day_of_year_frac - phase_frac))


@dataclass
class CampaignEvent:
    start_day_index: int  # seed dönemi başlangıcından itibaren gün sayısı
    duration_days: int
    intensity: float  # talep çarpanına eklenecek göreli şiddet (örn. 1.0 = +%100 civarı)


def generate_campaign_calendar(
    n_days: int, rng: np.random.Generator, avg_gap_days: int = 70
) -> list[CampaignEvent]:
    """
    Şirket geneli kampanya takvimi (tüm ürünleri aynı anda etkiler — pazarlama
    harcamasıyla satış artışı arasında gerçek, gecikmeli bir ilişki kurmak için
    ürün bazlı değil tek bir ortak takvim kullanılır).
    """
    events = []
    day = rng.integers(20, avg_gap_days)
    while day < n_days - 5:
        duration = int(rng.integers(3, 6))
        intensity = float(rng.uniform(0.6, 1.6))
        events.append(CampaignEvent(start_day_index=int(day), duration_days=duration, intensity=intensity))
        day += rng.integers(avg_gap_days - 20, avg_gap_days + 25)
    return events


def campaign_multiplier(day_index: int, campaigns: list[CampaignEvent], product_scale: float = 1.0) -> float:
    for c in campaigns:
        if c.start_day_index <= day_index < c.start_day_index + c.duration_days:
            return 1.0 + c.intensity * product_scale
    return 1.0
