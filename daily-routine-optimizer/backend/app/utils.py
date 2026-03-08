"""
Utility helpers used across the backend application.
"""

from datetime import datetime, timedelta
from typing import Optional


def get_week_bounds(reference_date: Optional[datetime] = None):
    """
    Get the Monday 00:00 and Sunday 23:59 of the week containing the reference date.

    Args:
        reference_date: Date to calculate week bounds for. Defaults to today.

    Returns:
        Tuple of (week_start, week_end) as datetime objects.
    """
    if reference_date is None:
        reference_date = datetime.utcnow()

    # Monday of the current week
    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Sunday end of the current week
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    return week_start, week_end


def calculate_delay_minutes(assigned_time: datetime, completed_at: datetime) -> float:
    """
    Calculate the delay in minutes between assigned time and completion time.

    Returns:
        Positive value = completed late, negative = completed early.
    """
    if not assigned_time or not completed_at:
        return 0.0
    delta = (completed_at - assigned_time).total_seconds() / 60.0
    return round(delta, 1)


def format_hour(hour: int) -> str:
    """
    Format an hour (0-23) as a readable time string.

    Examples:
        0  -> '12:00 AM'
        9  -> '9:00 AM'
        13 -> '1:00 PM'
        23 -> '11:00 PM'
    """
    if hour == 0:
        return "12:00 AM"
    elif hour < 12:
        return f"{hour}:00 AM"
    elif hour == 12:
        return "12:00 PM"
    else:
        return f"{hour - 12}:00 PM"


def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns default instead of raising ZeroDivisionError."""
    if denominator == 0:
        return default
    return round(numerator / denominator, 2)
