"""seed_data yardımcı modülleri için saf fonksiyon testleri — DB gerektirmez."""
from datetime import date

import numpy as np

from app.seed_data.calendar_effects import (
    generate_campaign_calendar,
    holiday_multiplier,
    is_holiday,
    weekly_multiplier,
)
from app.seed_data.customer_behavior import build_customer_profile, daily_purchase_probability


class TestCalendarEffects:
    def test_new_years_day_is_a_holiday(self):
        assert is_holiday(date(2025, 1, 1)) is True

    def test_ordinary_day_is_not_a_holiday(self):
        assert is_holiday(date(2025, 3, 3)) is False

    def test_holiday_multiplier_drops_demand_on_holiday(self):
        assert holiday_multiplier(date(2025, 1, 1)) < 1.0

    def test_weekly_multiplier_friday_higher_than_sunday(self):
        friday = date(2026, 1, 2)  # 2 Ocak 2026 bir Cuma
        sunday = date(2026, 1, 4)
        assert weekly_multiplier(friday) > weekly_multiplier(sunday)

    def test_campaign_calendar_events_within_bounds(self):
        rng = np.random.default_rng(0)
        events = generate_campaign_calendar(n_days=365, rng=rng)
        assert len(events) > 0
        for event in events:
            assert 0 <= event.start_day_index < 365
            assert event.duration_days >= 3


class TestCustomerBehavior:
    def test_churning_archetype_probability_decays_to_near_zero_over_time(self):
        rng = np.random.default_rng(0)
        n_days = 730
        # 'churning' arketipi bulana kadar dene (rastgele atama olduğu için)
        profile = None
        for _ in range(200):
            candidate = build_customer_profile(rng, n_days)
            if candidate.archetype == "churning":
                profile = candidate
                break
        assert profile is not None

        early_prob = daily_purchase_probability(profile, day_index=profile.signup_offset_days + 5, n_days=n_days)
        late_prob = daily_purchase_probability(profile, day_index=n_days - 1, n_days=n_days)
        assert late_prob < early_prob

    def test_purchase_probability_is_zero_before_signup(self):
        rng = np.random.default_rng(1)
        profile = build_customer_profile(rng, n_days=730)
        if profile.signup_offset_days > 0:
            assert daily_purchase_probability(profile, day_index=0, n_days=730) == 0.0
