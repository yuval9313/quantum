import asyncio
from uuid import UUID
import pytest
import redis.asyncio as redis_async
from starlette.testclient import TestClient

from quantum_api.main import app as api_app
from common.models import TaskStatus
from common.task_store import TaskStore
from common.tasks_broker import REDIS_URL
from common.dependencies import DATABASE_URL

pytestmark = pytest.mark.integration

VALID_QC = (
    'OPENQASM 3.0;\n'
    'include "stdgates.inc";\n'
    'bit[2] c;\n'
    'qubit[2] q;\n'
    'h q[0];\n'
    'cx q[0], q[1];\n'
    'c[0] = measure q[0];\n'
    'c[1] = measure q[1];\n'
)


@pytest.fixture
def api_client():
    with TestClient(api_app) as client:
        yield client


@pytest.fixture
async def redis_client():
    client = redis_async.from_url(REDIS_URL)
    yield client
    await client.aclose()


@pytest.fixture
async def db_store():
    store = TaskStore(DATABASE_URL)
    yield store
    await store.close()


@pytest.mark.anyio
@pytest.mark.integration
async def test_task_creation_and_pending_status(api_client, redis_client, db_store):
    """
    1. Create a task via POST /tasks.
    2. Verify task status is 'pending' in Postgres database.
    3. Verify task status is 'pending' via GET /tasks/{task_id} endpoint.
    4. Verify task message exists in Redis stream 'tasks'.
    """
    # 1. Post task to API
    post_response = api_client.post("/tasks", json={"qc": VALID_QC})
    assert post_response.status_code == 200
    response_data = post_response.json()
    assert "task_id" in response_data
    assert response_data["message"] == "Task submitted successfully."
    task_id_str = response_data["task_id"]
    task_id = UUID(task_id_str)

    # 2. Check Database directly for pending status
    db_record = await db_store.get(task_id)
    assert db_record is not None
    assert db_record.status == TaskStatus.PENDING
    assert db_record.qc == VALID_QC

    # 3. Check API GET endpoint for pending status
    get_response = api_client.get(f"/tasks/{task_id_str}")
    assert get_response.status_code == 200
    assert get_response.json() == {
        "status": "pending",
        "message": "Task is still in progress."
    }

    # 4. Check Redis stream 'tasks' for published task message
    stream_messages = await redis_client.xrange("tasks")
    found_in_stream = any(
        task_id_str in str(value) or task_id_str in str(key)
        for _, fields in stream_messages
        for key, value in fields.items()
    )
    assert found_in_stream, f"Task {task_id_str} was not found in Redis stream 'tasks'"


@pytest.mark.anyio
@pytest.mark.integration
async def test_task_full_flow_completion(api_client, db_store):
    """
    1. Submit a task via POST /tasks.
    2. Wait for quantum_service to process message from Redis stream.
    3. Verify task transitions to 'completed' status in Database and API response.
    4. Verify execution result contains non-empty result counts.
    """
    # 1. Post task to API
    post_response = api_client.post("/tasks", json={"qc": VALID_QC})
    assert post_response.status_code == 200
    task_id_str = post_response.json()["task_id"]
    task_id = UUID(task_id_str)

    # 2. Poll DB / API until status transitions from 'pending' to 'completed'
    completed_record = None
    max_retries = 20
    for _ in range(max_retries):
        record = await db_store.get(task_id)
        if record and record.status == TaskStatus.COMPLETED:
            completed_record = record
            break
        await asyncio.sleep(0.5)

    # 3. Assert DB record completed
    assert completed_record is not None, f"Task {task_id_str} did not transition to COMPLETED state within timeout"
    assert completed_record.status == TaskStatus.COMPLETED
    assert isinstance(completed_record.result, dict)
    assert len(completed_record.result) > 0

    # 4. Assert API GET endpoint returns completed status and result dict
    get_response = api_client.get(f"/tasks/{task_id_str}")
    assert get_response.status_code == 200
    api_data = get_response.json()
    assert api_data["status"] == "completed"
    assert api_data["result"] == completed_record.result
