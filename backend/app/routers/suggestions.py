"""
AI Suggestions API Router.

Exposes endpoints for getting ML-powered schedule suggestions
and personalized productivity insights.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import ml_engine

router = APIRouter(prefix="/api/suggestions", tags=["AI Suggestions"])


@router.get("/schedule")
def get_schedule_suggestions(db: Session = Depends(get_db)):
    """
    Get an AI-optimized schedule for all pending tasks.

    Returns a list of suggestions with optimal time slots,
    confidence scores, and reasoning for each recommendation.
    """
    suggestions = ml_engine.generate_schedule_suggestions(db)
    return {
        "suggestions": suggestions,
        "generated_at": datetime.utcnow().isoformat(),
        "model_available": ml_engine._load_model() is not None,
    }


@router.get("/insights")
def get_insights(db: Session = Depends(get_db)):
    """
    Get personalized productivity insights.

    Returns tips, warnings, and achievements based on
    the user's task completion patterns.
    """
    insights = ml_engine.generate_insights(db)
    return {
        "insights": insights,
        "generated_at": datetime.utcnow().isoformat(),
    }
