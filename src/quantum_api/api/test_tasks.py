from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from common.dependencies import get_task_store
from common.models import TaskRecord, TaskStatus

from .tasks import router as tasks_router


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(tasks_router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_get_task_completed(app, client):
    # Arrange
    task_id = uuid4()
    expected_response = {"status": "completed", "result": {"0": 512, "1": 512}}
    task_store = AsyncMock()
    task_store.get.return_value = TaskRecord(
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        qc="bell_state_circuit",
        created_at=datetime.now(UTC),
        result={"0": 512, "1": 512},
        updated_at=datetime.now(UTC),
        attempts=0,
        last_error=None,
    )
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    response = client.get(f"/tasks/{task_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


def test_get_task_pending(app, client):
    # Arrange
    task_id = uuid4()
    expected_response = {"status": "pending", "message": "Task is still in progress."}
    task_store = AsyncMock()
    task_store.get.return_value = TaskRecord(
        task_id=task_id,
        status=TaskStatus.PENDING,
        qc="bell_state_circuit",
        created_at=datetime.now(UTC),
        result={},
        updated_at=datetime.now(UTC),
        attempts=0,
        last_error=None,
    )
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    response = client.get(f"/tasks/{task_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


def test_get_task_not_found(app, client):
    # Arrange
    task_id = uuid4()
    expected_response = {"status": "error", "message": "Task not found."}
    task_store = AsyncMock()
    task_store.get.return_value = None
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    response = client.get(f"/tasks/{task_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == expected_response


def test_post_create_task_fails_on_invalid_input(app, client):
    # Arrange
    mock_task_id = uuid4()
    qc_payload = "bell_state_circuit"
    expected_response = {"status": "error", "message": "Invalid QASM3 code."}
    task_store = AsyncMock()
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    with patch("quantum_api.api.tasks.uuid4", return_value=mock_task_id):
        response = client.post("/tasks", json={"qc": qc_payload})

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == expected_response


def test_post_create_task_success(app, client):
    # Arrange
    mock_task_id = uuid4()
    qc_payload = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nbit[2] c;\nqubit[2] q;\nh q[0];\ncx q[0], q[1];\nc[0] = measure q[0];\nc[1] = measure q[1];\n'
    expected_response = {
        "task_id": str(mock_task_id),
        "message": "Task submitted successfully.",
    }
    task_store = AsyncMock()
    mock_publisher = AsyncMock()
    app.dependency_overrides[get_task_store] = lambda: task_store

    # Act
    with (
        patch("quantum_api.api.tasks.uuid4", return_value=mock_task_id),
        patch("common.tasks_broker.publisher", mock_publisher),
    ):
        response = client.post("/tasks", json={"qc": qc_payload})

    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == expected_response
    assert mock_publisher.publish.call_count == 1
