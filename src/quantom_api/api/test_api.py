from datetime import datetime, timezone
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from common.models import TaskRecord, TaskStatus
from .api import router
from .dependencies import get_task_store


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router, prefix="/tasks")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_get_task_completed(app, client):
    # Arrange
    task_id = uuid4()
    expected_response = {
        "status": "completed",
        "result": {"0": 512, "1": 512}
    }
    task_store = AsyncMock()
    task_store.get.return_value = TaskRecord(
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        qc="bell_state_circuit",
        created_at=datetime.now(timezone.utc),
        result={"0": 512, "1": 512},
        updated_at=datetime.now(timezone.utc),
        attempts=0,
        last_error=None,
    )
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    response = client.get(f"/tasks/{task_id}")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_response


def test_get_task_pending(app, client):
    # Arrange
    task_id = uuid4()
    expected_response = {
        "status": "pending",
        "message": "Task is still in progress."
    }
    task_store = AsyncMock()
    task_store.get.return_value = TaskRecord(
        task_id=task_id,
        status=TaskStatus.PENDING,
        qc="bell_state_circuit",
        created_at=datetime.now(timezone.utc),
        result={},
        updated_at=datetime.now(timezone.utc),
        attempts=0,
        last_error=None,
    )
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    response = client.get(f"/tasks/{task_id}")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_response


def test_get_task_not_found(app, client):
    # Arrange
    task_id = uuid4()
    expected_response = {
        "status": "error",
        "message": "Task not found."
    }
    task_store = AsyncMock()
    task_store.get.return_value = None
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    response = client.get(f"/tasks/{task_id}")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_response


def test_post_create_task(app, client):
    # Arrange
    mock_task_id = uuid4()
    qc_payload = "bell_state_circuit"
    expected_response = {
        "task_id": str(mock_task_id),
        "message": "Task submitted successfully."
    }
    task_store = AsyncMock()
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    with patch("quantom_api.api.api.uuid4", return_value=mock_task_id):
        response = client.post("/tasks", params={"qc": qc_payload})

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_response
