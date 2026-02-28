from __future__ import annotations

from datetime import datetime

import pandas as pd
from fastapi import FastAPI, HTTPException

from backend.app.database import get_connection, init_db
from backend.app.models import (
    AnalyticsResponse,
    SuggestionResponse,
    Task,
    TaskCreate,
    TaskUpdateStatus,
)
from backend.app.services.analytics import generate_analytics
from backend.app.services.ml import suggest_task_time, train_best_time_model

app = FastAPI(title="Daily Routine Optimizer API", version="1.0.0")


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks
            (title, description, priority, task_type, assigned_time, duration_minutes, reminder_minutes_before, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                task.title,
                task.description,
                task.priority,
                task.task_type,
                task.assigned_time.isoformat(),
                task.duration_minutes,
                task.reminder_minutes_before,
            ),
        )
        task_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO usage_logs (task_id, event_type, timestamp) VALUES (?, ?, ?)",
            (task_id, "created", datetime.utcnow().isoformat()),
        )

        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row)


@app.get("/tasks", response_model=list[Task])
def list_tasks(status: str | None = None):
    query = "SELECT * FROM tasks"
    params: tuple = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY assigned_time"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


@app.patch("/tasks/{task_id}/status", response_model=Task)
def update_task_status(task_id: int, payload: TaskUpdateStatus):
    with get_connection() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        completed_at = payload.completed_at.isoformat() if payload.completed_at else None
        if payload.status == "completed" and not completed_at:
            completed_at = datetime.utcnow().isoformat()

        conn.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (payload.status, completed_at, task_id),
        )
        conn.execute(
            "INSERT INTO usage_logs (task_id, event_type, timestamp) VALUES (?, ?, ?)",
            (task_id, f"status_{payload.status}", datetime.utcnow().isoformat()),
        )
        updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    return dict(updated)


@app.get("/analytics", response_model=AnalyticsResponse)
def get_analytics():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM tasks", conn)
    results = generate_analytics(df)
    filtered = {k: results[k] for k in AnalyticsResponse.model_fields.keys()}
    return filtered


@app.post("/ml/train")
def train_model():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM tasks", conn)
    metrics = train_best_time_model(df)
    return metrics


@app.get("/ml/suggestions", response_model=list[SuggestionResponse])
def get_suggestions():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM tasks", conn)

    analytics = generate_analytics(df)
    fallback = analytics.get("most_productive_hours", [9, 11, 14])

    suggestions = []
    for _, row in df[df["status"] == "pending"].iterrows():
        task_payload = {
            "priority": row["priority"],
            "duration_minutes": row["duration_minutes"],
            "assigned_weekday": pd.to_datetime(row["assigned_time"]).weekday(),
            "task_type": row["task_type"],
        }
        suggested = suggest_task_time(task_payload, fallback)
        suggestions.append({"task_id": int(row["id"]), **suggested})

    return suggestions
