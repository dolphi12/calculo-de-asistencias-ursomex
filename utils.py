"""Utility functions for time parsing and formatting."""

from datetime import datetime, timedelta
from typing import Optional
import math


def parse_time(value) -> Optional[datetime]:
    """Parse a time value from various formats into a datetime object (date part is ignored)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, timedelta):
        base = datetime(1900, 1, 1)
        return base + value
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def format_time(dt: Optional[datetime]) -> str:
    """Format a datetime as HH:MM string."""
    if dt is None:
        return ""
    return dt.strftime("%H:%M")


def minutes_between(start: Optional[datetime], end: Optional[datetime]) -> float:
    """Calculate minutes between two time values."""
    if start is None or end is None:
        return 0.0
    delta = end - start
    return delta.total_seconds() / 60.0


def minutes_to_hours(minutes: float) -> float:
    """Convert minutes to hours, rounded to 2 decimal places."""
    return round(minutes / 60.0, 2)


def apply_rounding(minutes: float, mode: str, rounding_minutes: int) -> float:
    """Apply rounding to a minutes value."""
    if mode == "none" or rounding_minutes <= 0:
        return minutes
    if mode == "ceil":
        return math.ceil(minutes / rounding_minutes) * rounding_minutes
    if mode == "floor":
        return math.floor(minutes / rounding_minutes) * rounding_minutes
    if mode == "round":
        return round(minutes / rounding_minutes) * rounding_minutes
    return minutes


def parse_permit_string(permit_str: str) -> list:
    """Parse a permit string like '14:30, 15:00, 18:30, 19:00' into list of datetime objects."""
    if not permit_str or str(permit_str).strip().lower() in ("", "nan"):
        return []
    parts = str(permit_str).split(",")
    result = []
    for part in parts:
        t = parse_time(part.strip())
        if t is not None:
            result.append(t)
    return result
