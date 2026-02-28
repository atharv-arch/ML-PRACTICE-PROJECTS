"""
Pydantic schemas for request/response validation.

These schemas decouple the API layer from the database models,
providing clean data contracts for all endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Task Schemas ───────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str = Field(default="", max_length=2000, description="Detailed description")
    category: str = Field(default="general", max_length=50, description="Task category")
    priority: int = Field(default=2, ge=1, le=5, description="Priority: 1 (low) to 5 (critical)")
    assigned_time: Optional[datetime] = Field(None, description="Scheduled start time")
    duration_minutes: int = Field(default=30, ge=1, le=480, description="Expected duration in minutes")
    reminder_minutes_before: int = Field(default=10, ge=0, le=120, description="Reminder offset in minutes")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task. All fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=50)
    priority: Optional[int] = Field(None, ge=1, le=5)
    assigned_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=480)
    reminder_minutes_before: Optional[int] = Field(None, ge=0, le=120)
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|missed)$")


class TaskResponse(BaseModel):
    """Schema for task data returned by the API."""
    id: int
    title: str
    description: str
    category: str
    priority: int
    assigned_time: Optional[datetime]
    duration_minutes: int
    reminder_minutes_before: int
    status: str
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""
    tasks: List[TaskResponse]
    total: int
    page: int
    per_page: int


# ── TaskLog Schemas ────────────────────────────────────────────────────────

class TaskLogResponse(BaseModel):
    """Schema for task log entries."""
    id: int
    task_id: int
    action: str
    timestamp: datetime
    notes: str

    model_config = {"from_attributes": True}


# ── Analytics Schemas ──────────────────────────────────────────────────────

class HourlyProductivity(BaseModel):
    """Productivity data for a single hour."""
    hour: int = Field(..., ge=0, le=23)
    completed_count: int
    total_count: int
    completion_rate: float


class DashboardStats(BaseModel):
    """Top-level dashboard statistics."""
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    missed_tasks: int
    completion_rate: float
    current_streak: int
    avg_delay_minutes: float
    most_productive_hour: int
    tasks_today: int
    completed_today: int


class CategoryStats(BaseModel):
    """Completion stats for a task category."""
    category: str
    total: int
    completed: int
    completion_rate: float
    avg_delay_minutes: float


class WeeklySummaryResponse(BaseModel):
    """Weekly summary with insights."""
    week_start: datetime
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    avg_delay_minutes: float
    most_productive_hour: int
    total_streaks: int
    recommendations: str  # JSON string

    model_config = {"from_attributes": True}


class StreakData(BaseModel):
    """Streak tracking information."""
    current_streak: int
    longest_streak: int
    streak_history: List[dict]


# ── AI Suggestion Schemas ─────────────────────────────────────────────────

class TaskSuggestion(BaseModel):
    """AI-generated suggestion for a single task."""
    task_title: str
    current_time: Optional[datetime]
    suggested_time: datetime
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str


class ScheduleSuggestions(BaseModel):
    """Complete AI-optimized schedule."""
    suggestions: List[TaskSuggestion]
    model_accuracy: Optional[float]
    generated_at: datetime


class InsightItem(BaseModel):
    """Single productivity insight."""
    type: str  # 'tip', 'warning', 'achievement'
    title: str
    description: str
    metric_value: Optional[float] = None


class InsightsResponse(BaseModel):
    """Collection of personalized insights."""
    insights: List[InsightItem]
    generated_at: datetime
