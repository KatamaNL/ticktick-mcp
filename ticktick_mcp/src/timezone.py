"""Timezone conversion for TickTick API.

TickTick stores all-day tasks as midnight UTC of the previous day,
adjusted for the user's timezone. For Europe/Amsterdam:
- CET (winter, ~Nov-Mar 28): {date-1}T23:00:00+0000
- CEST (summer, ~Mar 29-Oct): {date-1}T22:00:00+0000
"""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Amsterdam")

_ALIASES = {
    "vandaag": 0,
    "morgen": 1,
    "overmorgen": 2,
}


def parse_local_date(value: str) -> date:
    """Parse a local date string or Dutch alias to a date object.
    Accepts: "YYYY-MM-DD", "vandaag", "morgen", "overmorgen".
    """
    lower = value.strip().lower()
    if lower in _ALIASES:
        return date.today() + timedelta(days=_ALIASES[lower])
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(
            f"Invalid date '{value}'. Use YYYY-MM-DD, vandaag, morgen, or overmorgen."
        )


def to_ticktick_utc(d: date) -> str:
    """Convert a local date to TickTick all-day UTC string.
    Returns format: YYYY-MM-DDThh:mm:ss+0000
    """
    local_midnight = datetime(d.year, d.month, d.day, tzinfo=TZ)
    utc_midnight = local_midnight.astimezone(timezone.utc)
    return utc_midnight.strftime("%Y-%m-%dT%H:%M:%S+0000")


def from_ticktick_utc(utc_str: str | None) -> date | None:
    """Convert a TickTick UTC date string to local Amsterdam date."""
    if not utc_str:
        return None
    try:
        clean = utc_str.replace("+0000", "+00:00")
        dt = datetime.fromisoformat(clean)
        local = dt.astimezone(TZ)
        return local.date()
    except (ValueError, TypeError):
        return None


def format_local_date(utc_str: str | None) -> str:
    """Format a TickTick UTC date as a human-readable local date string."""
    d = from_ticktick_utc(utc_str)
    if d is None:
        return ""
    today = date.today()
    if d == today:
        return f"{d.isoformat()} (vandaag)"
    elif d == today + timedelta(days=1):
        return f"{d.isoformat()} (morgen)"
    elif d == today - timedelta(days=1):
        return f"{d.isoformat()} (gisteren)"
    return d.isoformat()
