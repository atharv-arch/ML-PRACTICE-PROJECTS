from datetime import datetime, timedelta

import pandas as pd

from backend.app.services.analytics import generate_analytics


def test_generate_analytics_basic():
    base = datetime(2026, 1, 1, 9, 0, 0)
    data = [
        {
            "id": 1,
            "title": "A",
            "description": "",
            "priority": 3,
            "task_type": "work",
            "assigned_time": base.isoformat(),
            "duration_minutes": 30,
            "status": "completed",
            "completed_at": (base + timedelta(minutes=20)).isoformat(),
        },
        {
            "id": 2,
            "title": "B",
            "description": "",
            "priority": 2,
            "task_type": "study",
            "assigned_time": (base + timedelta(hours=1)).isoformat(),
            "duration_minutes": 45,
            "status": "pending",
            "completed_at": None,
        },
    ]
    df = pd.DataFrame(data)
    metrics = generate_analytics(df)

    assert metrics["total_tasks"] == 2
    assert metrics["completed_tasks"] == 1
    assert metrics["completion_rate"] == 0.5
    assert "work" in metrics["completion_by_task_type"]
