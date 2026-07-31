from app.scheduler.scheduler import _parse_hhmm


class TestParseHhmm:
    def test_parses_hour_and_minute(self):
        assert _parse_hhmm("02:00") == (2, 0)

    def test_parses_non_zero_minute(self):
        assert _parse_hhmm("14:30") == (14, 30)
