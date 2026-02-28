from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.database import init_db
from backend.app.main import app

client = TestClient(app)


def setup_module():
    db = Path("data/routine_optimizer.db")
    if db.exists():
        db.unlink()
    init_db()


def test_task_lifecycle_and_analytics():
    assigned = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    response = client.post(
        "/tasks",
        json={
            "title": "Write report",
            "description": "Daily work report",
            "priority": 4,
            "task_type": "work",
            "assigned_time": assigned,
            "duration_minutes": 60,
            "reminder_minutes_before": 15,
        },
    )
    assert response.status_code == 200
    task_id = response.json()["id"]

    update_resp = client.patch(f"/tasks/{task_id}/status", json={"status": "completed"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "completed"

    analytics_resp = client.get("/analytics")
    assert analytics_resp.status_code == 200
    assert analytics_resp.json()["completed_tasks"] >= 1


def test_train_endpoint_with_seed_data():
    # Seed additional rows for training.
    tasks = []
    start = datetime(2026, 1, 1, 9)
    for i in range(12):
        assigned = start + timedelta(days=i, hours=i % 3)
        tasks.append(
            {
                "title": f"Task {i}",
                "description": "",
                "priority": 1 + (i % 5),
                "task_type": "work" if i % 2 == 0 else "study",
                "assigned_time": assigned.isoformat(),
                "duration_minutes": 30 + i,
                "reminder_minutes_before": 10,
            }
        )

    for task in tasks:
        created = client.post("/tasks", json=task).json()
        client.patch(
            f"/tasks/{created['id']}/status",
            json={"status": "completed", "completed_at": (pd.to_datetime(task['assigned_time']) + timedelta(hours=1)).isoformat()},
        )

    train_resp = client.post("/ml/train")
    assert train_resp.status_code == 200
    assert "best_model" in train_resp.json()
