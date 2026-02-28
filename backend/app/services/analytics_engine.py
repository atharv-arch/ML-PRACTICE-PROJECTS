"""
Analytics Engine — Core productivity metrics computation.

This service computes all productivity statistics by querying
the Task and TaskLog tables. Results power the dashboard,
analytics charts, and weekly summaries.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from app.models import Task, TaskLog, TaskStatus, WeeklySummary
from app.utils import get_week_bounds, calculate_delay_minutes, safe_division


def get_completion_rate(db: Session, start: Optional[datetime] = None, end: Optional[datetime] = None) -> float:
    """
    Calculate the percentage of completed tasks within a date range.

    Args:
        db: Database session
        start: Start of date range (default: 30 days ago)
        end: End of date range (default: now)

    Returns:
        Completion rate as a float between 0.0 and 100.0
    """
    if not start:
        start = datetime.utcnow() - timedelta(days=30)
    if not end:
        end = datetime.utcnow()

    total = db.query(Task).filter(
        and_(Task.created_at >= start, Task.created_at <= end)
    ).count()

    completed = db.query(Task).filter(
        and_(
            Task.created_at >= start,
            Task.created_at <= end,
            Task.status == TaskStatus.COMPLETED.value,
        )
    ).count()

    return safe_division(completed * 100, total)


def get_hourly_productivity(db: Session, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict]:
    """
    Get task completion count and rate for each hour of the day (0-23).

    Uses completion timestamps to determine which hours the user
    is most productive. Returns data suitable for a bar chart.
    """
    if not start:
        start = datetime.utcnow() - timedelta(days=30)
    if not end:
        end = datetime.utcnow()

    hourly_data = []

    for hour in range(24):
        # Count tasks assigned at this hour
        total = db.query(Task).filter(
            and_(
                Task.assigned_time.isnot(None),
                Task.created_at >= start,
                Task.created_at <= end,
                extract("hour", Task.assigned_time) == hour,
            )
        ).count()

        # Count tasks completed that were assigned at this hour
        completed = db.query(Task).filter(
            and_(
                Task.assigned_time.isnot(None),
                Task.created_at >= start,
                Task.created_at <= end,
                extract("hour", Task.assigned_time) == hour,
                Task.status == TaskStatus.COMPLETED.value,
            )
        ).count()

        hourly_data.append({
            "hour": hour,
            "completed_count": completed,
            "total_count": total,
            "completion_rate": safe_division(completed * 100, total),
        })

    return hourly_data


def get_most_productive_hours(db: Session, top_n: int = 3) -> List[int]:
    """
    Find the top N hours with the highest task completion counts.

    Returns a list of hours (0-23) sorted by completion count.
    """
    hourly = get_hourly_productivity(db)
    sorted_hours = sorted(hourly, key=lambda x: x["completed_count"], reverse=True)
    return [h["hour"] for h in sorted_hours[:top_n]]


def get_average_delay(db: Session, start: Optional[datetime] = None, end: Optional[datetime] = None) -> float:
    """
    Calculate the average delay (in minutes) between assigned and completion times.

    Positive values mean tasks were completed late.
    Only considers tasks that have both assigned_time and completed_at.
    """
    if not start:
        start = datetime.utcnow() - timedelta(days=30)
    if not end:
        end = datetime.utcnow()

    tasks = db.query(Task).filter(
        and_(
            Task.assigned_time.isnot(None),
            Task.completed_at.isnot(None),
            Task.status == TaskStatus.COMPLETED.value,
            Task.created_at >= start,
            Task.created_at <= end,
        )
    ).all()

    if not tasks:
        return 0.0

    delays = [calculate_delay_minutes(t.assigned_time, t.completed_at) for t in tasks]
    return round(sum(delays) / len(delays), 1)


def get_streak_data(db: Session) -> Dict:
    """
    Calculate streaks — consecutive days where completion rate >= 80%.

    Returns:
        Dictionary with current_streak, longest_streak, and daily history.
    """
    # Get the last 60 days of data
    end = datetime.utcnow()
    start = end - timedelta(days=60)

    # Group tasks by date
    tasks = db.query(Task).filter(
        and_(Task.created_at >= start, Task.created_at <= end)
    ).all()

    daily_stats = defaultdict(lambda: {"total": 0, "completed": 0})
    for task in tasks:
        day = task.created_at.strftime("%Y-%m-%d")
        daily_stats[day]["total"] += 1
        if task.status == TaskStatus.COMPLETED.value:
            daily_stats[day]["completed"] += 1

    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    streak_history = []

    # Iterate through dates in order
    current_date = start
    while current_date <= end:
        day_key = current_date.strftime("%Y-%m-%d")
        stats = daily_stats.get(day_key, {"total": 0, "completed": 0})

        if stats["total"] > 0:
            rate = safe_division(stats["completed"] * 100, stats["total"])
            passed = rate >= 80
        else:
            # No tasks = skip (don't break streak)
            passed = None

        if passed is True:
            temp_streak += 1
        elif passed is False:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 0

        streak_history.append({
            "date": day_key,
            "rate": safe_division(stats["completed"] * 100, stats["total"]) if stats["total"] > 0 else None,
            "in_streak": passed is True,
        })

        current_date += timedelta(days=1)

    current_streak = temp_streak
    longest_streak = max(longest_streak, current_streak)

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "streak_history": streak_history[-14:],  # Last 2 weeks
    }


def get_category_stats(db: Session, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict]:
    """
    Get completion statistics broken down by task category.

    Returns a list of category objects with total, completed, rate, and avg delay.
    """
    if not start:
        start = datetime.utcnow() - timedelta(days=30)
    if not end:
        end = datetime.utcnow()

    tasks = db.query(Task).filter(
        and_(Task.created_at >= start, Task.created_at <= end)
    ).all()

    categories = defaultdict(lambda: {"total": 0, "completed": 0, "delays": []})

    for task in tasks:
        cat = task.category or "general"
        categories[cat]["total"] += 1
        if task.status == TaskStatus.COMPLETED.value:
            categories[cat]["completed"] += 1
            if task.assigned_time and task.completed_at:
                delay = calculate_delay_minutes(task.assigned_time, task.completed_at)
                categories[cat]["delays"].append(delay)

    result = []
    for cat, stats in categories.items():
        delays = stats["delays"]
        avg_delay = round(sum(delays) / len(delays), 1) if delays else 0.0
        result.append({
            "category": cat,
            "total": stats["total"],
            "completed": stats["completed"],
            "completion_rate": safe_division(stats["completed"] * 100, stats["total"]),
            "avg_delay_minutes": avg_delay,
        })

    return sorted(result, key=lambda x: x["total"], reverse=True)


def get_dashboard_stats(db: Session) -> Dict:
    """
    Compute the top-level dashboard statistics.

    Combines completion rate, streak, task counts, delay, and
    productive hour data into a single response.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59)

    total = db.query(Task).count()
    completed = db.query(Task).filter(Task.status == TaskStatus.COMPLETED.value).count()
    pending = db.query(Task).filter(Task.status == TaskStatus.PENDING.value).count()
    missed = db.query(Task).filter(Task.status == TaskStatus.MISSED.value).count()

    tasks_today = db.query(Task).filter(
        and_(Task.assigned_time >= today_start, Task.assigned_time <= today_end)
    ).count()
    completed_today = db.query(Task).filter(
        and_(
            Task.assigned_time >= today_start,
            Task.assigned_time <= today_end,
            Task.status == TaskStatus.COMPLETED.value,
        )
    ).count()

    streaks = get_streak_data(db)
    productive_hours = get_most_productive_hours(db, top_n=1)
    avg_delay = get_average_delay(db)

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "missed_tasks": missed,
        "completion_rate": safe_division(completed * 100, total),
        "current_streak": streaks["current_streak"],
        "avg_delay_minutes": avg_delay,
        "most_productive_hour": productive_hours[0] if productive_hours else 9,
        "tasks_today": tasks_today,
        "completed_today": completed_today,
    }


def get_weekly_comparison(db: Session) -> List[Dict]:
    """
    Compare productivity across the last 4 weeks.

    Returns weekly stats for trend detection and comparison charts.
    """
    now = datetime.utcnow()
    weeks = []

    for i in range(4):
        week_end = now - timedelta(weeks=i)
        week_start, week_end_dt = get_week_bounds(week_end)

        total = db.query(Task).filter(
            and_(Task.created_at >= week_start, Task.created_at <= week_end_dt)
        ).count()

        completed = db.query(Task).filter(
            and_(
                Task.created_at >= week_start,
                Task.created_at <= week_end_dt,
                Task.status == TaskStatus.COMPLETED.value,
            )
        ).count()

        weeks.append({
            "week_start": week_start.isoformat(),
            "week_label": f"Week {4 - i}",
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": safe_division(completed * 100, total),
        })

    return list(reversed(weeks))


def generate_weekly_summary(db: Session) -> Dict:
    """
    Generate and store a comprehensive weekly summary.

    Includes completion rate, delays, productive hours, streaks,
    and auto-generated personalized recommendations.
    """
    week_start, week_end = get_week_bounds()

    # Compute all stats
    completion_rate = get_completion_rate(db, week_start, week_end)
    avg_delay = get_average_delay(db, week_start, week_end)
    productive_hours = get_most_productive_hours(db, top_n=3)
    streaks = get_streak_data(db)
    category_stats = get_category_stats(db, week_start, week_end)

    total = db.query(Task).filter(
        and_(Task.created_at >= week_start, Task.created_at <= week_end)
    ).count()
    completed = db.query(Task).filter(
        and_(
            Task.created_at >= week_start,
            Task.created_at <= week_end,
            Task.status == TaskStatus.COMPLETED.value,
        )
    ).count()

    # Generate recommendations based on patterns
    recommendations = _generate_recommendations(
        completion_rate, avg_delay, productive_hours, category_stats
    )

    # Upsert the weekly summary
    existing = db.query(WeeklySummary).filter(
        WeeklySummary.week_start == week_start
    ).first()

    summary_data = {
        "week_start": week_start,
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_rate": completion_rate,
        "avg_delay_minutes": avg_delay,
        "most_productive_hour": productive_hours[0] if productive_hours else 9,
        "total_streaks": streaks["current_streak"],
        "recommendations": json.dumps(recommendations),
    }

    if existing:
        for key, value in summary_data.items():
            setattr(existing, key, value)
        summary = existing
    else:
        summary = WeeklySummary(**summary_data)
        db.add(summary)

    db.commit()
    db.refresh(summary)
    return summary_data


def _generate_recommendations(
    completion_rate: float,
    avg_delay: float,
    productive_hours: List[int],
    category_stats: List[Dict],
) -> List[Dict]:
    """
    Generate personalized recommendations based on analytics data.

    Uses rule-based logic to create actionable suggestions.
    """
    recs = []

    # Completion rate recommendations
    if completion_rate < 50:
        recs.append({
            "type": "warning",
            "title": "Low Completion Rate",
            "description": f"Your completion rate is {completion_rate:.0f}%. Try reducing the number of tasks or breaking them into smaller pieces.",
        })
    elif completion_rate >= 90:
        recs.append({
            "type": "achievement",
            "title": "Excellent Productivity!",
            "description": f"You're completing {completion_rate:.0f}% of your tasks. Keep up the great work!",
        })

    # Delay recommendations
    if avg_delay > 30:
        recs.append({
            "type": "tip",
            "title": "Tasks Running Late",
            "description": f"Tasks are averaging {avg_delay:.0f} minutes late. Consider adding buffer time between tasks.",
        })
    elif avg_delay < 0:
        recs.append({
            "type": "achievement",
            "title": "Ahead of Schedule!",
            "description": f"You're finishing tasks {abs(avg_delay):.0f} minutes early on average. Great time management!",
        })

    # Productive hours recommendation
    if productive_hours:
        from app.utils import format_hour
        hours_str = ", ".join(format_hour(h) for h in productive_hours[:3])
        recs.append({
            "type": "tip",
            "title": "Your Peak Hours",
            "description": f"You're most productive at {hours_str}. Schedule important tasks during these times.",
        })

    # Category-based recommendations
    for cat in category_stats:
        if cat["total"] >= 3 and cat["completion_rate"] < 40:
            recs.append({
                "type": "warning",
                "title": f"Low '{cat['category']}' Completion",
                "description": f"Only {cat['completion_rate']:.0f}% of your '{cat['category']}' tasks are getting done. Consider adjusting priorities.",
            })

    return recs
