from __future__ import annotations

import pandas as pd


def preprocess_tasks(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich task data for analytics/model training."""
    if df.empty:
        return df

    clean_df = df.copy()
    clean_df["assigned_time"] = pd.to_datetime(clean_df["assigned_time"], errors="coerce")
    clean_df["completed_at"] = pd.to_datetime(clean_df.get("completed_at"), errors="coerce")
    clean_df["priority"] = clean_df["priority"].fillna(3).astype(int)
    clean_df["duration_minutes"] = clean_df["duration_minutes"].fillna(30).astype(int)
    clean_df["task_type"] = clean_df["task_type"].fillna("general")
    clean_df["status"] = clean_df["status"].fillna("pending")

    clean_df = clean_df.dropna(subset=["assigned_time"])

    clean_df["assigned_hour"] = clean_df["assigned_time"].dt.hour
    clean_df["assigned_weekday"] = clean_df["assigned_time"].dt.weekday
    clean_df["completed_hour"] = clean_df["completed_at"].dt.hour

    clean_df["delay_minutes"] = (
        (clean_df["completed_at"] - clean_df["assigned_time"]).dt.total_seconds() / 60
    ).fillna(0)

    clean_df["completed_flag"] = (clean_df["status"] == "completed").astype(int)
    return clean_df
