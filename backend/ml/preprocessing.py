"""
Preprocessing Pipeline — Feature engineering for ML model training.

Transforms raw task data into features suitable for training
a classifier that predicts optimal task scheduling hours.

Features extracted:
    - priority: task priority level (1-5)
    - duration_minutes: expected task duration
    - category_encoded: one-hot or label-encoded category
    - day_of_week: 0=Monday to 6=Sunday
    - is_weekend: binary flag for Saturday/Sunday
    - assigned_hour: hour the task was originally assigned
    - historical_completion_rate: user's completion rate at that hour
    - hour_sin / hour_cos: cyclical encoding of hour
    - day_sin / day_cos: cyclical encoding of day of week
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple, Optional


def load_data(csv_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load task data from CSV file.

    Args:
        csv_path: Path to the CSV file. Defaults to data/sample_tasks.csv

    Returns:
        DataFrame with raw task data
    """
    if csv_path is None:
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "sample_tasks.csv"
        )

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Data file not found: {csv_path}\n"
            "Run 'python -m ml.generate_sample_data' first."
        )

    df = pd.read_csv(csv_path, parse_dates=["assigned_time", "completed_at", "created_at"])
    print(f"📊 Loaded {len(df)} records from {csv_path}")
    return df


def handle_missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in the dataset.

    Strategy:
        - Fill missing descriptions with empty string
        - Fill missing categories with 'general'
        - Fill missing durations with median
        - Drop rows with missing assigned_time (critical feature)
    """
    df = df.copy()

    # Fill text columns
    df["description"] = df["description"].fillna("")
    df["category"] = df["category"].fillna("general")

    # Fill numeric columns with median
    df["duration_minutes"] = df["duration_minutes"].fillna(df["duration_minutes"].median())
    df["priority"] = df["priority"].fillna(2)
    df["reminder_minutes_before"] = df["reminder_minutes_before"].fillna(10)

    # Drop rows without assigned time (can't train without this)
    initial_len = len(df)
    df = df.dropna(subset=["assigned_time"])
    dropped = initial_len - len(df)
    if dropped > 0:
        print(f"⚠️  Dropped {dropped} rows with missing assigned_time")

    return df


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract ML features from the raw task data.

    Creates both linear and cyclical time encodings,
    category encodings, and historical performance metrics.
    """
    df = df.copy()

    # ── Time features ──────────────────────────────────────────────
    df["assigned_hour"] = df["assigned_time"].dt.hour
    df["day_of_week"] = df["assigned_time"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Cyclical encoding for hours (captures that 23:00 is close to 0:00)
    df["hour_sin"] = np.sin(2 * np.pi * df["assigned_hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["assigned_hour"] / 24)

    # Cyclical encoding for day of week
    df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # ── Category encoding ──────────────────────────────────────────
    category_map = {
        "work": 0, "health": 1, "personal": 2,
        "learning": 3, "errands": 4, "general": 5,
    }
    df["category_encoded"] = df["category"].map(category_map).fillna(5).astype(int)

    # ── Historical completion rate per hour ─────────────────────────
    # Compute the user's average completion rate at each hour of the day
    df["is_completed"] = (df["status"] == "completed").astype(int)
    hourly_rates = df.groupby("assigned_hour")["is_completed"].mean()
    df["historical_hour_rate"] = df["assigned_hour"].map(hourly_rates).fillna(0.5)

    # ── Target variable ────────────────────────────────────────────
    # For completed tasks: the actual completion hour = optimal hour
    # For incomplete tasks: we exclude them from training
    df["optimal_hour"] = df["assigned_hour"]  # Default to assigned hour
    if "completed_at" in df.columns:
        completed_mask = df["completed_at"].notna()
        if completed_mask.any():
            df.loc[completed_mask, "optimal_hour"] = pd.to_datetime(
                df.loc[completed_mask, "completed_at"]
            ).dt.hour

    print(f"✅ Extracted {df.shape[1]} features from {df.shape[0]} records")
    return df


def prepare_training_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Prepare feature matrix X and target vector y for model training.

    Only uses completed tasks for training (they have confirmed optimal hours).

    Args:
        df: DataFrame with extracted features

    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (optimal_hour, 0-23)
        feature_names: List of feature column names
    """
    # Filter to completed tasks only
    train_df = df[df["status"] == "completed"].copy()

    if len(train_df) < 10:
        raise ValueError(
            f"Not enough completed tasks for training ({len(train_df)}). "
            "Need at least 10 completed tasks."
        )

    # Define feature columns
    feature_cols = [
        "priority",
        "duration_minutes",
        "category_encoded",
        "day_of_week",
        "is_weekend",
        "hour_sin",
        "hour_cos",
        "day_sin",
        "day_cos",
        "historical_hour_rate",
    ]

    X = train_df[feature_cols].values.astype(np.float64)
    y = train_df["optimal_hour"].values.astype(int)

    # Clamp target to valid range
    y = np.clip(y, 0, 23)

    print(f"📐 Training data: X shape={X.shape}, y shape={y.shape}")
    print(f"   Target distribution: {np.bincount(y, minlength=24)[:24]}")
    return X, y, feature_cols


def preprocess_pipeline(csv_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, list, pd.DataFrame]:
    """
    Full preprocessing pipeline: load → clean → extract → prepare.

    Returns:
        X, y, feature_names, processed_dataframe
    """
    df = load_data(csv_path)
    df = handle_missing_data(df)
    df = extract_features(df)
    X, y, feature_names = prepare_training_data(df)
    return X, y, feature_names, df


if __name__ == "__main__":
    X, y, names, df = preprocess_pipeline()
    print(f"\n📊 Pipeline complete!")
    print(f"   Features: {names}")
    print(f"   Samples: {X.shape[0]}")
    print(f"   Feature count: {X.shape[1]}")
