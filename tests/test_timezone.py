import pytest
from datetime import date, timedelta
from ticktick_mcp.src.timezone import (
    parse_local_date,
    to_ticktick_utc,
    from_ticktick_utc,
    format_local_date,
)


class TestParseLocalDate:
    def test_iso_date(self):
        assert parse_local_date("2026-03-23") == date(2026, 3, 23)

    def test_vandaag(self):
        assert parse_local_date("vandaag") == date.today()

    def test_morgen(self):
        assert parse_local_date("morgen") == date.today() + timedelta(days=1)

    def test_overmorgen(self):
        assert parse_local_date("overmorgen") == date.today() + timedelta(days=2)

    def test_case_insensitive(self):
        assert parse_local_date("Vandaag") == date.today()
        assert parse_local_date("MORGEN") == date.today() + timedelta(days=1)

    def test_whitespace(self):
        assert parse_local_date("  2026-03-23  ") == date(2026, 3, 23)

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid date"):
            parse_local_date("blabla")


class TestToTickTickUtc:
    def test_cet_winter(self):
        # March 23, 2026 is CET (before DST switch March 29)
        result = to_ticktick_utc(date(2026, 3, 23))
        assert result == "2026-03-22T23:00:00+0000"

    def test_cest_summer(self):
        # April 1, 2026 is CEST (after DST switch March 29)
        result = to_ticktick_utc(date(2026, 4, 1))
        assert result == "2026-03-31T22:00:00+0000"

    def test_dst_boundary(self):
        # March 29, 2026: DST switch happens at 02:00 local time, so midnight is still CET (UTC+1)
        # The clocks move forward at 02:00 on March 29, so midnight March 29 is still CET
        result = to_ticktick_utc(date(2026, 3, 29))
        assert result == "2026-03-28T23:00:00+0000"

    def test_dst_boundary_after(self):
        # March 30, 2026 is the first full day of CEST (UTC+2)
        result = to_ticktick_utc(date(2026, 3, 30))
        assert result == "2026-03-29T22:00:00+0000"

    def test_december_cet(self):
        result = to_ticktick_utc(date(2026, 12, 25))
        assert result == "2026-12-24T23:00:00+0000"

    def test_new_years_day(self):
        result = to_ticktick_utc(date(2026, 1, 1))
        assert result == "2025-12-31T23:00:00+0000"


class TestFromTickTickUtc:
    def test_cet_winter(self):
        result = from_ticktick_utc("2026-03-22T23:00:00.000+0000")
        assert result == date(2026, 3, 23)

    def test_cest_summer(self):
        result = from_ticktick_utc("2026-03-31T22:00:00.000+0000")
        assert result == date(2026, 4, 1)

    def test_none_input(self):
        assert from_ticktick_utc(None) is None

    def test_empty_string(self):
        assert from_ticktick_utc("") is None

    def test_timed_task_afternoon(self):
        # 14:00 CET = 13:00 UTC on March 23
        result = from_ticktick_utc("2026-03-23T13:00:00.000+0000")
        assert result == date(2026, 3, 23)

    def test_invalid_string(self):
        assert from_ticktick_utc("not-a-date") is None


class TestFormatLocalDate:
    def test_none(self):
        assert format_local_date(None) == ""

    def test_regular_date(self):
        # A date far in the future - just returns ISO format
        result = format_local_date("2027-06-14T22:00:00.000+0000")
        assert result == "2027-06-15"
