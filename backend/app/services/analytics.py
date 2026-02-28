from __future__ import annotations

from datetime import datetime

import pandas as pd

from backend.app.services.preprocess import preprocess_tasks


def compute_streak(completed_dates: list[datetime.date]) -> int:
    if not completed_dates:
        return 0
    streak = 1
    best = 1
    for i in range(1, len(completed_dates)):
        if (completed_dates[i] - completed_dates[i - 1]).days == 1:
            streak += 1
            best = max(best, streak)
        elif completed_dates[i] != completed_dates[i - 1]:
            streak = 1
    return best


def generate_analytics(tasks_df: pd.DataFrame) -> dict:
    if tasks_df.empty:
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "completion_rate": 0.0,
            "most_productive_hours": [],
            "average_delay_minutes": 0.0,
            "missed_tasks": 0,
            "streak_days": 0,
            "completion_by_hour": {},
            "completion_by_task_type": {},
            "week_over_week_completion": {},
        }

    df = preprocess_tasks(tasks_df)
    total_tasks = len(df)
    completed = df[df["completed_flag"] == 1]
    completed_tasks = len(completed)

    completion_by_hour = (
        completed.groupby("completed_hour")["completed_flag"].count().sort_values(ascending=False)
    )
    productive_hours = [int(h) for h in completion_by_hour.head(3).index.tolist() if pd.notna(h)]

    completion_by_task_type = (
        df.groupby("task_type")["completed_flag"].mean().round(3).to_dict()
    )

    now = pd.Timestamp(datetime.utcnow())
    missed_tasks = int(
        ((df["status"] == "pending") & (df["assigned_time"] < now)).sum()
    )

    avg_delay = float(completed["delay_minutes"].mean()) if completed_tasks else 0.0

    completed_dates = sorted(
        completed["completed_at"].dropna().dt.date.unique().tolist()
    )
    streak_days = compute_streak(completed_dates)

    wow = (
        df.assign(week=df["assigned_time"].dt.isocalendar().week)
        .groupby("week")["completed_flag"]
        .mean()
        .round(3)
        .to_dict()
    )

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": round(completed_tasks / total_tasks, 3),
        "most_productive_hours": productive_hours,
        "average_delay_minutes": round(avg_delay, 2),
        "missed_tasks": missed_tasks,
        "streak_days": streak_days,
        "completion_by_hour": {str(int(k)): int(v) for k, v in completion_by_hour.to_dict().items() if pd.notna(k)},
        "completion_by_task_type": completion_by_task_type,
        "week_over_week_completion": {str(int(k)): float(v) for k, v in wow.items()},
    }
