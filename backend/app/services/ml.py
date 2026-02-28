from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from backend.app.services.preprocess import preprocess_tasks

MODEL_PATH = Path("models/best_time_model.joblib")


def train_best_time_model(df: pd.DataFrame) -> dict:
    processed = preprocess_tasks(df)
    completed = processed[processed["completed_flag"] == 1].dropna(subset=["completed_hour"])
    if len(completed) < 10:
        raise ValueError("Need at least 10 completed tasks to train model.")

    features = ["priority", "duration_minutes", "assigned_weekday", "task_type"]
    target = completed["completed_hour"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        completed[features], target, test_size=0.25, random_state=42, stratify=target
    )

    preprocessor = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), ["task_type"])],
        remainder="passthrough",
    )

    rf_model = Pipeline(
        steps=[("prep", preprocessor), ("clf", RandomForestClassifier(n_estimators=200, random_state=42))]
    )
    lr_model = Pipeline(
        steps=[("prep", preprocessor), ("clf", LogisticRegression(max_iter=1200, multi_class="auto"))]
    )

    rf_model.fit(X_train, y_train)
    lr_model.fit(X_train, y_train)

    rf_acc = accuracy_score(y_test, rf_model.predict(X_test))
    lr_acc = accuracy_score(y_test, lr_model.predict(X_test))

    best_name = "random_forest" if rf_acc >= lr_acc else "logistic_regression"
    best_model = rf_model if best_name == "random_forest" else lr_model

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)

    return {
        "best_model": best_name,
        "random_forest_accuracy": round(float(rf_acc), 3),
        "logistic_regression_accuracy": round(float(lr_acc), 3),
        "trained_samples": int(len(completed)),
    }


def suggest_task_time(task: dict, fallback_hours: list[int] | None = None) -> dict:
    fallback_hours = fallback_hours or [9, 11, 14]
    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)
        sample = pd.DataFrame(
            [
                {
                    "priority": int(task.get("priority", 3)),
                    "duration_minutes": int(task.get("duration_minutes", 30)),
                    "assigned_weekday": int(task.get("assigned_weekday", 0)),
                    "task_type": task.get("task_type", "general"),
                }
            ]
        )
        pred_hour = int(model.predict(sample)[0])
        reason = "ML model predicted peak completion hour from historical behavior."
    else:
        pred_hour = int(np.median(fallback_hours))
        reason = "No trained model found; used productivity-hour fallback from analytics."

    suggested_priority = max(1, min(5, int(task.get("priority", 3))))
    return {
        "suggested_hour": pred_hour,
        "suggested_priority": suggested_priority,
        "reason": reason,
    }
