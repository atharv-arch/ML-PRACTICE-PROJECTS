"""
ML Engine Service — Machine Learning prediction and suggestion pipeline.

Loads a trained model (if available) to predict optimal task scheduling.
Falls back to rule-based suggestions when no model is trained yet.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

import numpy as np
from sqlalchemy.orm import Session

from app.models import Task, TaskStatus
from app.services.analytics_engine import get_most_productive_hours, get_category_stats

logger = logging.getLogger(__name__)

# Path to the trained model artifact
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")


def _load_model():
    """
    Attempt to load the trained ML model from disk.
    Returns None if model file doesn't exist or loading fails.
    """
    try:
        import joblib
        if os.path.exists(MODEL_PATH):
            model_data = joblib.load(MODEL_PATH)
            logger.info("ML model loaded successfully")
            return model_data
        else:
            logger.info("No trained model found — using rule-based suggestions")
            return None
    except Exception as e:
        logger.warning(f"Failed to load ML model: {e}")
        return None


def _extract_task_features(task: Task) -> Dict:
    """
    Extract feature vector from a task for ML prediction.

    Features:
        - priority: task priority (1-5)
        - duration: task duration in minutes
        - category_hash: numeric encoding of category
        - day_of_week: 0=Monday ... 6=Sunday
        - current_hour: hour when prediction is made
    """
    now = datetime.utcnow()
    category_hash = hash(task.category or "general") % 10

    return {
        "priority": task.priority,
        "duration_minutes": task.duration_minutes,
        "category_encoded": category_hash,
        "day_of_week": now.weekday(),
        "current_hour": now.hour,
    }


def predict_best_time(task: Task, db: Session) -> Dict:
    """
    Predict the optimal time slot for completing a task.

    Strategy:
        1. If a trained model exists, use ML prediction
        2. Otherwise, fall back to rule-based heuristics based on
           historical productivity patterns

    Returns:
        Dictionary with suggested_hour, confidence, and reason
    """
    model_data = _load_model()

    if model_data and "model" in model_data:
        # ── ML-based prediction ────────────────────────────────────
        model = model_data["model"]
        features = _extract_task_features(task)
        feature_array = np.array([[
            features["priority"],
            features["duration_minutes"],
            features["category_encoded"],
            features["day_of_week"],
            features["current_hour"],
        ]])

        try:
            predicted_hour = int(model.predict(feature_array)[0])
            # Get prediction probabilities if available
            confidence = 0.75
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(feature_array)
                confidence = float(np.max(proba))

            return {
                "suggested_hour": predicted_hour,
                "confidence": round(confidence, 2),
                "reason": f"ML model predicts optimal completion at hour {predicted_hour} based on your patterns",
                "model_used": True,
                "model_accuracy": model_data.get("accuracy", None),
            }
        except Exception as e:
            logger.warning(f"ML prediction failed, falling back to rules: {e}")

    # ── Rule-based fallback ────────────────────────────────────────
    return _rule_based_prediction(task, db)


def _rule_based_prediction(task: Task, db: Session) -> Dict:
    """
    Generate suggestions using rule-based heuristics when no ML model is available.

    Rules:
        1. High priority tasks → schedule in most productive hours
        2. Long tasks → schedule in the morning (when energy is highest)
        3. Low priority tasks → schedule in less busy hours
        4. Use historical productive hours from analytics
    """
    productive_hours = get_most_productive_hours(db, top_n=5)

    # Default productive hours if no data
    if not productive_hours or all(h == 0 for h in productive_hours):
        productive_hours = [9, 10, 14, 15, 11]

    priority = task.priority
    duration = task.duration_minutes

    if priority >= 4:
        # High priority → first productive hour
        suggested = productive_hours[0] if productive_hours else 9
        reason = "High priority — scheduled during your most productive hour"
        confidence = 0.8
    elif duration >= 60:
        # Long task → morning slot
        suggested = min(productive_hours[:3]) if productive_hours else 9
        reason = "Long task — scheduled in the morning when focus is highest"
        confidence = 0.7
    elif priority <= 2:
        # Low priority → afternoon
        afternoon_hours = [h for h in productive_hours if h >= 13]
        suggested = afternoon_hours[0] if afternoon_hours else 14
        reason = "Low priority — scheduled for afternoon to keep mornings free"
        confidence = 0.6
    else:
        # Medium → second most productive hour
        suggested = productive_hours[1] if len(productive_hours) > 1 else 10
        reason = "Scheduled during a productive time slot"
        confidence = 0.65

    return {
        "suggested_hour": suggested,
        "confidence": round(confidence, 2),
        "reason": reason,
        "model_used": False,
        "model_accuracy": None,
    }


def generate_schedule_suggestions(db: Session, tasks: Optional[List[Task]] = None) -> List[Dict]:
    """
    Generate an AI-optimized full-day schedule.

    Takes all pending tasks (or a provided list) and assigns
    optimal time slots, avoiding overlaps and respecting durations.

    Args:
        db: Database session
        tasks: Optional list of tasks. If None, fetches all pending tasks.

    Returns:
        List of suggestion dictionaries, one per task.
    """
    if tasks is None:
        tasks = db.query(Task).filter(
            Task.status == TaskStatus.PENDING.value
        ).order_by(Task.priority.desc()).all()

    if not tasks:
        return []

    suggestions = []
    occupied_hours = set()

    # Sort by priority (high first) then duration (long first)
    sorted_tasks = sorted(tasks, key=lambda t: (-t.priority, -t.duration_minutes))

    for task in sorted_tasks:
        prediction = predict_best_time(task, db)
        suggested_hour = prediction["suggested_hour"]

        # Avoid double-booking: shift to nearest free hour
        attempts = 0
        while suggested_hour in occupied_hours and attempts < 12:
            suggested_hour = (suggested_hour + 1) % 24
            attempts += 1

        # Mark hours as occupied (based on task duration)
        hours_needed = max(1, task.duration_minutes // 60)
        for h in range(hours_needed):
            occupied_hours.add((suggested_hour + h) % 24)

        # Build the suggested datetime
        now = datetime.utcnow()
        suggested_time = now.replace(
            hour=suggested_hour, minute=0, second=0, microsecond=0
        )
        if suggested_time < now:
            suggested_time += timedelta(days=1)

        suggestions.append({
            "task_id": task.id,
            "task_title": task.title,
            "current_time": task.assigned_time.isoformat() if task.assigned_time else None,
            "suggested_time": suggested_time.isoformat(),
            "suggested_hour": suggested_hour,
            "confidence": prediction["confidence"],
            "reason": prediction["reason"],
            "model_used": prediction["model_used"],
            "priority": task.priority,
            "duration_minutes": task.duration_minutes,
        })

    return suggestions


def generate_insights(db: Session) -> List[Dict]:
    """
    Generate personalized productivity insights.

    Analyzes patterns to produce actionable tips, warnings, and achievements.
    """
    insights = []
    productive_hours = get_most_productive_hours(db, top_n=3)
    category_stats = get_category_stats(db)

    # Time management insight
    if productive_hours:
        from app.utils import format_hour
        peak = format_hour(productive_hours[0])
        insights.append({
            "type": "tip",
            "title": "Peak Performance Window",
            "description": f"Your data shows you're most productive at {peak}. Schedule your most important tasks during this window.",
            "metric_value": productive_hours[0],
        })

    # Category efficiency insight
    best_cat = max(category_stats, key=lambda x: x["completion_rate"]) if category_stats else None
    if best_cat and best_cat["total"] >= 2:
        insights.append({
            "type": "achievement",
            "title": f"'{best_cat['category']}' Champion",
            "description": f"You complete {best_cat['completion_rate']:.0f}% of your '{best_cat['category']}' tasks. This is your strongest category!",
            "metric_value": best_cat["completion_rate"],
        })

    # Worst category insight
    worst_cat = min(category_stats, key=lambda x: x["completion_rate"]) if category_stats else None
    if worst_cat and worst_cat["total"] >= 3 and worst_cat["completion_rate"] < 50:
        insights.append({
            "type": "warning",
            "title": f"Struggling with '{worst_cat['category']}'",
            "description": f"Only {worst_cat['completion_rate']:.0f}% completion for '{worst_cat['category']}' tasks. Try breaking them into smaller subtasks.",
            "metric_value": worst_cat["completion_rate"],
        })

    # Model availability insight
    model_data = _load_model()
    if model_data:
        accuracy = model_data.get("accuracy", 0)
        insights.append({
            "type": "tip",
            "title": "AI Model Active",
            "description": f"Your personal AI model is trained with {accuracy*100:.0f}% accuracy. Suggestions are based on your actual patterns.",
            "metric_value": accuracy,
        })
    else:
        insights.append({
            "type": "tip",
            "title": "Building Your AI Profile",
            "description": "Keep completing tasks! After enough data, an ML model will be trained to give you personalized schedule suggestions.",
            "metric_value": None,
        })

    return insights
