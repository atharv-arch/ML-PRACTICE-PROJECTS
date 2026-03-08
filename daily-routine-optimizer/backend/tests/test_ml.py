"""
Unit tests for the ML Module.

Tests preprocessing pipeline, feature extraction,
and model prediction output format.
"""

import os
import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from ml.preprocessing import (
    handle_missing_data,
    extract_features,
    prepare_training_data,
)


# ── Test Data ──────────────────────────────────────────────────────────────

def create_test_dataframe(n_rows=50):
    """Create a test DataFrame mimicking the sample data format."""
    np.random.seed(42)

    categories = ["work", "health", "personal", "learning", "errands"]
    statuses = ["completed", "pending", "missed"]

    data = {
        "title": [f"Task {i}" for i in range(n_rows)],
        "description": [f"Description {i}" if i % 3 != 0 else None for i in range(n_rows)],
        "category": [categories[i % len(categories)] for i in range(n_rows)],
        "priority": np.random.randint(1, 6, size=n_rows),
        "assigned_time": pd.date_range("2024-01-01", periods=n_rows, freq="3h"),
        "duration_minutes": np.random.choice([15, 30, 45, 60, 90], size=n_rows),
        "reminder_minutes_before": [10 if i % 2 == 0 else None for i in range(n_rows)],
        "status": [statuses[i % 3] for i in range(n_rows)],
        "completed_at": [None] * n_rows,
        "created_at": pd.date_range("2024-01-01", periods=n_rows, freq="3h") - pd.Timedelta(hours=1),
    }

    df = pd.DataFrame(data)

    # Fill completed_at for completed tasks
    mask = df["status"] == "completed"
    df.loc[mask, "completed_at"] = df.loc[mask, "assigned_time"] + pd.Timedelta(minutes=40)

    return df


# ── Tests ──────────────────────────────────────────────────────────────────

class TestMissingDataHandling:
    """Tests for the missing data handler."""

    def test_fills_none_descriptions(self):
        """Should fill None descriptions with empty string."""
        df = create_test_dataframe()
        result = handle_missing_data(df)
        assert result["description"].isna().sum() == 0

    def test_fills_none_reminders(self):
        """Should fill None reminder values."""
        df = create_test_dataframe()
        result = handle_missing_data(df)
        assert result["reminder_minutes_before"].isna().sum() == 0

    def test_preserves_valid_data(self):
        """Should not modify valid data."""
        df = create_test_dataframe()
        original_len = len(df)
        result = handle_missing_data(df)
        assert len(result) == original_len  # No rows dropped

    def test_drops_missing_assigned_time(self):
        """Should drop rows where assigned_time is None."""
        df = create_test_dataframe()
        df.loc[0, "assigned_time"] = None
        result = handle_missing_data(df)
        assert len(result) == len(df) - 1


class TestFeatureExtraction:
    """Tests for feature extraction pipeline."""

    def test_creates_time_features(self):
        """Should create hour and day features."""
        df = create_test_dataframe()
        df = handle_missing_data(df)
        result = extract_features(df)

        assert "assigned_hour" in result.columns
        assert "day_of_week" in result.columns
        assert "is_weekend" in result.columns

    def test_creates_cyclical_features(self):
        """Should create sin/cos cyclical encodings."""
        df = create_test_dataframe()
        df = handle_missing_data(df)
        result = extract_features(df)

        assert "hour_sin" in result.columns
        assert "hour_cos" in result.columns
        assert "day_sin" in result.columns
        assert "day_cos" in result.columns

        # Verify cyclical range [-1, 1]
        assert result["hour_sin"].between(-1, 1).all()
        assert result["hour_cos"].between(-1, 1).all()

    def test_category_encoding(self):
        """Should encode categories as integers."""
        df = create_test_dataframe()
        df = handle_missing_data(df)
        result = extract_features(df)

        assert "category_encoded" in result.columns
        assert result["category_encoded"].dtype in [np.int32, np.int64]

    def test_historical_hour_rate(self):
        """Should compute historical completion rate per hour."""
        df = create_test_dataframe()
        df = handle_missing_data(df)
        result = extract_features(df)

        assert "historical_hour_rate" in result.columns
        assert result["historical_hour_rate"].between(0, 1).all()

    def test_target_variable(self):
        """Should create optimal_hour target variable."""
        df = create_test_dataframe()
        df = handle_missing_data(df)
        result = extract_features(df)

        assert "optimal_hour" in result.columns
        assert result["optimal_hour"].between(0, 23).all()


class TestTrainingDataPreparation:
    """Tests for training data matrix preparation."""

    def test_output_shapes(self):
        """Should produce correctly shaped X and y arrays."""
        df = create_test_dataframe(n_rows=100)
        df = handle_missing_data(df)
        df = extract_features(df)
        X, y, feature_names = prepare_training_data(df)

        assert X.ndim == 2
        assert y.ndim == 1
        assert X.shape[0] == y.shape[0]
        assert X.shape[1] == len(feature_names)

    def test_only_completed_tasks(self):
        """Should only include completed tasks in training data."""
        df = create_test_dataframe(n_rows=100)
        df = handle_missing_data(df)
        df = extract_features(df)
        completed_count = (df["status"] == "completed").sum()
        X, y, _ = prepare_training_data(df)

        assert X.shape[0] == completed_count

    def test_target_range(self):
        """Target values should be valid hours (0-23)."""
        df = create_test_dataframe(n_rows=100)
        df = handle_missing_data(df)
        df = extract_features(df)
        _, y, _ = prepare_training_data(df)

        assert y.min() >= 0
        assert y.max() <= 23

    def test_feature_names(self):
        """Should return expected feature names."""
        df = create_test_dataframe(n_rows=100)
        df = handle_missing_data(df)
        df = extract_features(df)
        _, _, feature_names = prepare_training_data(df)

        expected = [
            "priority", "duration_minutes", "category_encoded",
            "day_of_week", "is_weekend", "hour_sin", "hour_cos",
            "day_sin", "day_cos", "historical_hour_rate",
        ]
        assert feature_names == expected

    def test_insufficient_data_raises(self):
        """Should raise ValueError with too few completed tasks."""
        df = create_test_dataframe(n_rows=5)
        df["status"] = "pending"  # No completed tasks
        df = handle_missing_data(df)
        df = extract_features(df)

        with pytest.raises(ValueError, match="Not enough completed tasks"):
            prepare_training_data(df)
