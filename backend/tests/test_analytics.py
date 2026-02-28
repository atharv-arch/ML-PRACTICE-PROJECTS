"""
Unit tests for the Analytics Engine.

Tests productivity calculations with known data sets
to verify correctness of metrics.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Task, TaskLog, TaskStatus
from app.services import analytics_engine
from app.utils import calculate_delay_minutes, safe_division, format_hour, get_week_bounds


# ── Test Database Setup ────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///./test_analytics.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def add_task(db, title="Test", status="completed", category="work", priority=3,
             assigned_hour=9, completed_delay=10, days_ago=0):
    """Helper: create a task with computed timestamps."""
    now = datetime.utcnow() - timedelta(days=days_ago)
    assigned = now.replace(hour=assigned_hour, minute=0, second=0)
    completed_at = None
    if status == "completed":
        completed_at = assigned + timedelta(minutes=30 + completed_delay)

    task = Task(
        title=title, status=status, category=category, priority=priority,
        assigned_time=assigned, duration_minutes=30,
        completed_at=completed_at, created_at=now,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# ── Utility Tests ──────────────────────────────────────────────────────────

class TestUtilities:
    """Tests for utility helper functions."""

    def test_calculate_delay_positive(self):
        """Positive delay = completed after assigned time."""
        assigned = datetime(2024, 1, 1, 9, 0)
        completed = datetime(2024, 1, 1, 9, 45)
        assert calculate_delay_minutes(assigned, completed) == 45.0

    def test_calculate_delay_negative(self):
        """Negative delay = completed before assigned time."""
        assigned = datetime(2024, 1, 1, 9, 0)
        completed = datetime(2024, 1, 1, 8, 45)
        assert calculate_delay_minutes(assigned, completed) == -15.0

    def test_calculate_delay_none(self):
        """Should return 0 when inputs are None."""
        assert calculate_delay_minutes(None, datetime.utcnow()) == 0.0
        assert calculate_delay_minutes(datetime.utcnow(), None) == 0.0

    def test_safe_division(self):
        assert safe_division(10, 2) == 5.0
        assert safe_division(1, 3) == 0.33
        assert safe_division(10, 0) == 0.0
        assert safe_division(0, 0, default=-1) == -1

    def test_format_hour(self):
        assert format_hour(0) == "12:00 AM"
        assert format_hour(9) == "9:00 AM"
        assert format_hour(12) == "12:00 PM"
        assert format_hour(13) == "1:00 PM"
        assert format_hour(23) == "11:00 PM"

    def test_get_week_bounds(self):
        # Test with a known Wednesday
        wed = datetime(2024, 1, 3, 14, 30)
        start, end = get_week_bounds(wed)
        assert start.weekday() == 0  # Monday
        assert start.hour == 0
        assert end.weekday() == 6    # Sunday


# ── Analytics Engine Tests ─────────────────────────────────────────────────

class TestCompletionRate:
    """Tests for completion rate calculation."""

    def test_empty_database(self, db_session):
        """Should return 0 for empty database."""
        rate = analytics_engine.get_completion_rate(db_session)
        assert rate == 0.0

    def test_all_completed(self, db_session):
        """Should return 100% when all tasks are completed."""
        for i in range(5):
            add_task(db_session, title=f"Task {i}", status="completed")
        rate = analytics_engine.get_completion_rate(db_session)
        assert rate == 100.0

    def test_mixed_statuses(self, db_session):
        """Should calculate correct rate with mixed statuses."""
        for i in range(3):
            add_task(db_session, title=f"Done {i}", status="completed")
        for i in range(2):
            add_task(db_session, title=f"Pending {i}", status="pending")
        rate = analytics_engine.get_completion_rate(db_session)
        assert rate == 60.0


class TestHourlyProductivity:
    """Tests for hourly productivity breakdown."""

    def test_returns_24_hours(self, db_session):
        """Should return data for all 24 hours."""
        result = analytics_engine.get_hourly_productivity(db_session)
        assert len(result) == 24

    def test_correct_hour_data(self, db_session):
        """Should count completions in the correct hour."""
        add_task(db_session, assigned_hour=9, status="completed")
        add_task(db_session, assigned_hour=9, status="completed")
        add_task(db_session, assigned_hour=14, status="pending")

        result = analytics_engine.get_hourly_productivity(db_session)
        hour_9 = next(h for h in result if h["hour"] == 9)
        assert hour_9["completed_count"] == 2


class TestStreaks:
    """Tests for streak calculation."""

    def test_empty_streaks(self, db_session):
        """Should return zero streaks for empty database."""
        streaks = analytics_engine.get_streak_data(db_session)
        assert streaks["current_streak"] == 0
        assert streaks["longest_streak"] == 0

    def test_streak_calculation(self, db_session):
        """Should detect consecutive productive days."""
        # Create 3 consecutive days with 100% completion
        for day in range(3):
            for i in range(3):
                add_task(db_session, title=f"Day {day} Task {i}",
                        status="completed", days_ago=day)

        streaks = analytics_engine.get_streak_data(db_session)
        assert streaks["current_streak"] >= 1


class TestCategoryStats:
    """Tests for category breakdown."""

    def test_empty_categories(self, db_session):
        """Should return empty list for no tasks."""
        result = analytics_engine.get_category_stats(db_session)
        assert result == []

    def test_multiple_categories(self, db_session):
        """Should break down stats by category."""
        add_task(db_session, category="work", status="completed")
        add_task(db_session, category="work", status="pending")
        add_task(db_session, category="health", status="completed")

        result = analytics_engine.get_category_stats(db_session)
        assert len(result) == 2

        work = next(c for c in result if c["category"] == "work")
        assert work["total"] == 2
        assert work["completed"] == 1
        assert work["completion_rate"] == 50.0


class TestDashboardStats:
    """Tests for the aggregated dashboard stats."""

    def test_dashboard_empty(self, db_session):
        """Should return zeros for empty database."""
        stats = analytics_engine.get_dashboard_stats(db_session)
        assert stats["total_tasks"] == 0
        assert stats["completion_rate"] == 0.0

    def test_dashboard_with_data(self, db_session):
        """Should compute correct aggregated stats."""
        add_task(db_session, status="completed")
        add_task(db_session, status="pending")
        add_task(db_session, status="missed")

        stats = analytics_engine.get_dashboard_stats(db_session)
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 1
        assert stats["pending_tasks"] == 1
        assert stats["missed_tasks"] == 1
