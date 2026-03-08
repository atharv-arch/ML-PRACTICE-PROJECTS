"""
Unit tests for Task CRUD API endpoints.

Tests all task operations: create, read, update, complete,
delete, and filtering.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db


# ── Test Database Setup ────────────────────────────────────────────────────

# Use in-memory SQLite for tests (fast, isolated)
TEST_DATABASE_URL = "sqlite:///./test_tasks.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_sample_task(**overrides):
    """Helper: create a task via the API and return the response."""
    default = {
        "title": "Test Task",
        "description": "A test task description",
        "category": "work",
        "priority": 3,
        "assigned_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "duration_minutes": 30,
        "reminder_minutes_before": 10,
    }
    default.update(overrides)
    response = client.post("/api/tasks/", json=default)
    return response


# ── Tests ──────────────────────────────────────────────────────────────────

class TestCreateTask:
    """Tests for POST /api/tasks/"""

    def test_create_task_success(self):
        """Should create a task and return 201."""
        response = create_sample_task(title="Morning Exercise")
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Morning Exercise"
        assert data["status"] == "pending"
        assert data["id"] is not None

    def test_create_task_minimal(self):
        """Should create a task with only required fields."""
        response = client.post("/api/tasks/", json={"title": "Quick Task"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Quick Task"
        assert data["category"] == "general"
        assert data["priority"] == 2

    def test_create_task_empty_title(self):
        """Should reject task with empty title."""
        response = client.post("/api/tasks/", json={"title": ""})
        assert response.status_code == 422  # Validation error

    def test_create_task_invalid_priority(self):
        """Should reject priority outside 1-5 range."""
        response = client.post("/api/tasks/", json={"title": "Task", "priority": 10})
        assert response.status_code == 422


class TestListTasks:
    """Tests for GET /api/tasks/"""

    def test_list_empty(self):
        """Should return empty list when no tasks exist."""
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["tasks"] == []

    def test_list_with_tasks(self):
        """Should return all created tasks."""
        create_sample_task(title="Task 1")
        create_sample_task(title="Task 2")
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_filter_by_status(self):
        """Should filter tasks by status."""
        create_sample_task(title="Pending Task")
        response = client.get("/api/tasks/?status=pending")
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert all(t["status"] == "pending" for t in tasks)

    def test_filter_by_category(self):
        """Should filter tasks by category."""
        create_sample_task(title="Work Task", category="work")
        create_sample_task(title="Health Task", category="health")
        response = client.get("/api/tasks/?category=work")
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert all(t["category"] == "work" for t in tasks)

    def test_pagination(self):
        """Should support pagination."""
        for i in range(5):
            create_sample_task(title=f"Task {i}")
        response = client.get("/api/tasks/?page=1&per_page=2")
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1


class TestGetTask:
    """Tests for GET /api/tasks/{id}"""

    def test_get_existing_task(self):
        """Should return task details by ID."""
        created = create_sample_task(title="Specific Task").json()
        response = client.get(f"/api/tasks/{created['id']}")
        assert response.status_code == 200
        assert response.json()["title"] == "Specific Task"

    def test_get_nonexistent_task(self):
        """Should return 404 for non-existent task."""
        response = client.get("/api/tasks/9999")
        assert response.status_code == 404


class TestUpdateTask:
    """Tests for PUT /api/tasks/{id}"""

    def test_update_task(self):
        """Should update specified fields."""
        created = create_sample_task(title="Original").json()
        response = client.put(
            f"/api/tasks/{created['id']}",
            json={"title": "Updated Title", "priority": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["priority"] == 5

    def test_update_nonexistent(self):
        """Should return 404 for non-existent task."""
        response = client.put("/api/tasks/9999", json={"title": "Nope"})
        assert response.status_code == 404


class TestCompleteTask:
    """Tests for PATCH /api/tasks/{id}/complete"""

    def test_complete_task(self):
        """Should mark task as completed with timestamp."""
        created = create_sample_task().json()
        response = client.patch(f"/api/tasks/{created['id']}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_complete_already_completed(self):
        """Should reject completing an already completed task."""
        created = create_sample_task().json()
        client.patch(f"/api/tasks/{created['id']}/complete")
        response = client.patch(f"/api/tasks/{created['id']}/complete")
        assert response.status_code == 400


class TestDeleteTask:
    """Tests for DELETE /api/tasks/{id}"""

    def test_delete_task(self):
        """Should delete the task and return 204."""
        created = create_sample_task().json()
        response = client.delete(f"/api/tasks/{created['id']}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/tasks/{created['id']}")
        assert get_response.status_code == 404

    def test_delete_nonexistent(self):
        """Should return 404 for non-existent task."""
        response = client.delete("/api/tasks/9999")
        assert response.status_code == 404
