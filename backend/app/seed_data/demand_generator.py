"""
Ürün bazlı, gerçekçi günlük talep serisi üretimi:
taban_oran * trend * haftalık * yıllık * tatil * kampanya + Poisson gürültüsü.
"""
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

from app.seed_data.calendar_effects import (
    CampaignEvent,
    annual_multiplier,
    campaign_multiplier,
    holiday_multiplier,
    weekly_multiplier,
)


@dataclass
class ProductDemandProfile:
    base_rate: float
    trend_per_day: float
    seasonality_amplitude: float
    seasonality_phase_month: float
    campaign_sensitivity: float  # 0=kampanyalardan etkilenmez, 1=tam güçle etkilenir


def sample_product_demand_profile(category: str, rng: np.random.Generator) -> ProductDemandProfile:
    """Kategoriye göre kaba bir taban talep/mevsimsellik yapısı, ürüne özgü rastgelelikle."""
    category_base = {
        "Gıda": (14.0, 0.35),
        "Tekstil": (6.0, 0.30),
        "Elektronik": (4.0, 0.20),
        "Kozmetik": (7.0, 0.25),
        "Ev & Yaşam": (5.0, 0.20),
    }
    base_rate, base_amplitude = category_base.get(category, (6.0, 0.25))

    return ProductDemandProfile(
        base_rate=float(base_rate * rng.uniform(0.6, 1.6)),
        trend_per_day=float(rng.uniform(-0.0006, 0.0015)),
        seasonality_amplitude=float(base_amplitude * rng.uniform(0.7, 1.3)),
        seasonality_phase_month=float(rng.uniform(1, 12)),
        campaign_sensitivity=float(rng.uniform(0.5, 1.3)),
    )


def generate_daily_demand(
    start_date: date,
    n_days: int,
    profile: ProductDemandProfile,
    campaigns: list[CampaignEvent],
    rng: np.random.Generator,
) -> list[int]:
    """n_days uzunluğunda, trend+mevsimsellik+kampanya+tatil+gürültü içeren tam sayı talep serisi."""
    demand = []
    for t in range(n_days):
        d = start_date + timedelta(days=t)
        expected = profile.base_rate * (1 + profile.trend_per_day * t)
        expected *= weekly_multiplier(d)
        expected *= annual_multiplier(d, profile.seasonality_amplitude, profile.seasonality_phase_month)
        expected *= holiday_multiplier(d)
        expected *= campaign_multiplier(t, campaigns, profile.campaign_sensitivity)
        expected = max(expected, 0.05)
        qty = int(rng.poisson(expected))
        demand.append(qty)
    return demand
