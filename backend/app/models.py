from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = ""
    priority: int = Field(ge=1, le=5, default=3)
    task_type: str = "general"
    assigned_time: datetime
    duration_minutes: int = Field(gt=0, default=30)
    reminder_minutes_before: Optional[int] = Field(default=None, ge=0)


class Task(TaskCreate):
    id: int
    status: str
    completed_at: Optional[datetime] = None


class TaskUpdateStatus(BaseModel):
    status: str = Field(pattern="^(pending|completed)$")
    completed_at: Optional[datetime] = None


class AnalyticsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    most_productive_hours: list[int]
    average_delay_minutes: float
    missed_tasks: int
    streak_days: int
    completion_by_hour: dict
    completion_by_task_type: dict


class SuggestionResponse(BaseModel):
    task_id: int
    suggested_hour: int
    suggested_priority: int
    reason: str
