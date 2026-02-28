"""
Task CRUD API Router.

Provides endpoints for creating, reading, updating, and deleting tasks.
All state changes are logged to the TaskLog table for analytics.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models import Task, TaskLog, TaskStatus
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


# ── CREATE ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """
    Create a new task and log the creation event.

    - Validates input via Pydantic schema
    - Creates the task in the database
    - Records a 'created' entry in the task log
    """
    task = Task(
        title=task_data.title,
        description=task_data.description,
        category=task_data.category,
        priority=task_data.priority,
        assigned_time=task_data.assigned_time,
        duration_minutes=task_data.duration_minutes,
        reminder_minutes_before=task_data.reminder_minutes_before,
        status=TaskStatus.PENDING.value,
    )
    db.add(task)
    db.flush()  # Get the task ID before creating the log

    # Log the creation
    log = TaskLog(task_id=task.id, action="created", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(task)
    return task


# ── READ (LIST) ────────────────────────────────────────────────────────────

@router.get("/", response_model=TaskListResponse)
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[int] = Query(None, ge=1, le=5, description="Filter by priority"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List tasks with optional filters and pagination.

    Supports filtering by status, category, priority, and date.
    Results are ordered by assigned_time (upcoming first), then by priority.
    """
    query = db.query(Task)

    # Apply filters
    filters = []
    if status:
        filters.append(Task.status == status)
    if category:
        filters.append(Task.category == category)
    if priority:
        filters.append(Task.priority == priority)
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            next_day = target_date.replace(hour=23, minute=59, second=59)
            filters.append(and_(Task.assigned_time >= target_date, Task.assigned_time <= next_day))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if filters:
        query = query.filter(and_(*filters))

    # Count total before pagination
    total = query.count()

    # Order and paginate
    tasks = (
        query.order_by(Task.assigned_time.asc().nullslast(), Task.priority.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return TaskListResponse(tasks=tasks, total=total, page=page, per_page=per_page)


# ── READ (SINGLE) ─────────────────────────────────────────────────────────

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a single task by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ── UPDATE ─────────────────────────────────────────────────────────────────

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):
    """
    Update a task's fields. Only provided fields are updated.
    Logs an 'updated' event in the task log.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update only the fields that were provided
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()

    # Log the update
    log = TaskLog(task_id=task.id, action="updated", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(task)
    return task


# ── MARK COMPLETE ──────────────────────────────────────────────────────────

@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Mark a task as completed with the current timestamp.

    - Sets status to 'completed'
    - Records the completion time
    - Logs a 'completed' event for analytics
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == TaskStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Task is already completed")

    task.status = TaskStatus.COMPLETED.value
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()

    # Log completion
    log = TaskLog(task_id=task.id, action="completed", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(task)
    return task


# ── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Delete a task and all its associated logs.
    Uses cascade delete defined in the ORM relationship.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return None


# ── TASK LOGS ──────────────────────────────────────────────────────────────

@router.get("/{task_id}/logs", response_model=list)
def get_task_logs(task_id: int, db: Session = Depends(get_db)):
    """Get the full action log for a specific task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    logs = (
        db.query(TaskLog)
        .filter(TaskLog.task_id == task_id)
        .order_by(TaskLog.timestamp.desc())
        .all()
    )
    return [
        {
            "id": log.id,
            "task_id": log.task_id,
            "action": log.action,
            "timestamp": log.timestamp.isoformat(),
            "notes": log.notes,
        }
        for log in logs
    ]
