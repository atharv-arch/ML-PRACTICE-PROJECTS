"""
SQLAlchemy ORM models for the Daily Routine Optimizer.

Models:
    - Task: core task entity with scheduling and status tracking
    - TaskLog: audit trail of all task state changes with timestamps
    - WeeklySummary: pre-computed weekly analytics snapshots
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────

class TaskStatus(str, enum.Enum):
    """Possible states for a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"


class TaskPriority(int, enum.Enum):
    """Priority levels from low (1) to critical (5)."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class LogAction(str, enum.Enum):
    """Types of actions recorded in the task log."""
    CREATED = "created"
    STARTED = "started"
    COMPLETED = "completed"
    MISSED = "missed"
    SNOOZED = "snoozed"
    UPDATED = "updated"


# ── Task Model ─────────────────────────────────────────────────────────────

class Task(Base):
    """
    Core task entity representing a single unit of work.

    Attributes:
        title: Short name of the task
        description: Optional detailed description
        category: Grouping label (e.g., 'work', 'health', 'personal')
        priority: 1 (low) to 5 (critical)
        assigned_time: When the task is scheduled to start
        duration_minutes: Expected time to complete
        reminder_minutes_before: Optional reminder offset (minutes before assigned_time)
        status: Current task state (pending/in_progress/completed/missed)
        completed_at: Timestamp when the task was actually completed
        created_at: Timestamp when the task was created
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, default="")
    category = Column(String(50), default="general", index=True)
    priority = Column(Integer, default=2)  # 1-5
    assigned_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=30)
    reminder_minutes_before = Column(Integer, default=10)
    status = Column(String(20), default=TaskStatus.PENDING.value, index=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to task logs
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


# ── TaskLog Model ──────────────────────────────────────────────────────────

class TaskLog(Base):
    """
    Audit log for tracking every state change of a task.
    Used by the analytics engine to compute productivity metrics.

    Attributes:
        task_id: Foreign key to the parent task
        action: Type of action (created/started/completed/missed/snoozed)
        timestamp: When the action occurred
        notes: Optional context for the action
    """
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text, default="")

    # Back-reference to the parent task
    task = relationship("Task", back_populates="logs")

    def __repr__(self):
        return f"<TaskLog(task_id={self.task_id}, action='{self.action}')>"


# ── WeeklySummary Model ────────────────────────────────────────────────────

class WeeklySummary(Base):
    """
    Pre-computed weekly analytics snapshot.
    Generated once per week by the analytics engine.

    Attributes:
        week_start: Start date of the summary week (Monday)
        total_tasks: Number of tasks scheduled that week
        completed_tasks: Number of tasks completed
        completion_rate: Percentage of tasks completed
        avg_delay_minutes: Average delay in minutes for completed tasks
        most_productive_hour: Hour of day (0-23) with highest completion rate
        total_streaks: Number of consecutive high-productivity days
        recommendations: JSON string of personalized recommendations
    """
    __tablename__ = "weekly_summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    week_start = Column(DateTime, nullable=False, index=True)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    avg_delay_minutes = Column(Float, default=0.0)
    most_productive_hour = Column(Integer, default=9)
    total_streaks = Column(Integer, default=0)
    recommendations = Column(Text, default="[]")  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WeeklySummary(week={self.week_start}, rate={self.completion_rate:.1f}%)>"
