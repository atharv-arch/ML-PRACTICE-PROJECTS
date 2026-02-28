"""
Analytics API Router.

Exposes productivity metrics, hourly data, streaks,
category breakdowns, and weekly summaries.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analytics_engine

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """
    Get top-level dashboard statistics.

    Returns overall completion rate, streak data, task counts,
    average delay, and most productive hour.
    """
    return analytics_engine.get_dashboard_stats(db)


@router.get("/hourly")
def get_hourly_productivity(db: Session = Depends(get_db)):
    """
    Get task completion data broken down by hour of day (0-23).
    Used to render the hourly productivity bar chart.
    """
    return analytics_engine.get_hourly_productivity(db)


@router.get("/categories")
def get_category_stats(db: Session = Depends(get_db)):
    """
    Get completion stats broken down by task category.
    Used for the category breakdown doughnut chart.
    """
    return analytics_engine.get_category_stats(db)


@router.get("/streaks")
def get_streaks(db: Session = Depends(get_db)):
    """
    Get streak information — consecutive productive days.
    Includes current streak, longest streak, and daily history.
    """
    return analytics_engine.get_streak_data(db)


@router.get("/weekly-summary")
def get_weekly_summary(db: Session = Depends(get_db)):
    """
    Generate and return the current week's summary.
    Includes auto-generated recommendations.
    """
    return analytics_engine.generate_weekly_summary(db)


@router.get("/weekly-comparison")
def get_weekly_comparison(db: Session = Depends(get_db)):
    """
    Compare productivity across the last 4 weeks.
    Returns weekly stats for trend charts.
    """
    return analytics_engine.get_weekly_comparison(db)
