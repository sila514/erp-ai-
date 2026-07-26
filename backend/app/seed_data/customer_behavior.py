"""
Müşteri arketipleri: her müşteri `loyal` / `new` / `at_risk` / `churning`
arketiplerinden birine atanır ve 2 yıllık dönem boyunca günlük satın alma
olasılık eğrisi bu arketipe göre şekillenir. `churning` arketipi olasılığı
zamanla kademeli olarak sıfıra indirir — gerçekçi bir churn sinyali için.
"""
from dataclasses import dataclass
from typing import Literal

import numpy as np

Archetype = Literal["loyal", "new", "at_risk", "churning"]

ARCHETYPE_WEIGHTS: dict[Archetype, float] = {
    "loyal": 0.35,
    "new": 0.20,
    "at_risk": 0.20,
    "churning": 0.25,
}


@dataclass
class CustomerProfile:
    archetype: Archetype
    base_daily_prob: float
    signup_offset_days: int  # 0 = dönem başından beri müşteri
    avg_basket_size: float  # ortalama sepet büyüklüğü çarpanı (bazı müşteriler daha çok harcar)


def build_customer_profile(rng: np.random.Generator, n_days: int) -> CustomerProfile:
    archetypes = list(ARCHETYPE_WEIGHTS.keys())
    weights = list(ARCHETYPE_WEIGHTS.values())
    archetype: Archetype = rng.choice(archetypes, p=weights)

    if archetype == "loyal":
        base_prob = rng.uniform(0.035, 0.07)
        signup_offset = int(rng.integers(0, n_days // 6))
    elif archetype == "new":
        base_prob = rng.uniform(0.04, 0.08)
        signup_offset = int(rng.integers(int(n_days * 0.75), n_days - 10))
    elif archetype == "at_risk":
        base_prob = rng.uniform(0.015, 0.03)
        signup_offset = int(rng.integers(0, n_days // 3))
    else:  # churning
        base_prob = rng.uniform(0.035, 0.06)
        signup_offset = int(rng.integers(0, n_days // 4))

    return CustomerProfile(
        archetype=archetype,
        base_daily_prob=float(base_prob),
        signup_offset_days=signup_offset,
        avg_basket_size=float(rng.uniform(0.7, 1.8)),
    )


def daily_purchase_probability(profile: CustomerProfile, day_index: int, n_days: int) -> float:
    """Belirli bir gün için satın alma olasılığı — arketipe göre zamanla değişir."""
    if day_index < profile.signup_offset_days:
        return 0.0

    days_active = day_index - profile.signup_offset_days
    active_span = max(n_days - profile.signup_offset_days, 1)

    if profile.archetype == "churning":
        # İlk %40'lık dilimde normal davranış, ardından olasılık kademeli olarak sıfıra düşer.
        decay_start = active_span * 0.4
        if days_active < decay_start:
            return profile.base_daily_prob
        decay_progress = (days_active - decay_start) / max(active_span - decay_start, 1)
        return profile.base_daily_prob * max(0.0, 1 - decay_progress) ** 1.5

    if profile.archetype == "new":
        # Katılımdan sonraki ilk ay ivme kazanır.
        ramp = min(1.0, days_active / 30)
        return profile.base_daily_prob * (0.3 + 0.7 * ramp)

    return profile.base_daily_prob
