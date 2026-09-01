from typing import Annotated

from fast_depends import Depends
from faststream import FastStream, Logger

from common.dependencies import get_task_store
from common.models import TaskMessage, TaskStatus
from common.task_store import TaskStore
from common.tasks_broker import broker, tasks_stream

from .core import execute_circuit_with_retry

TaskStoreDep = Annotated[TaskStore, Depends(get_task_store)]

app = FastStream(broker)

@broker.subscriber(stream=tasks_stream)
async def handle_task(msg: TaskMessage, logger: Logger, store: TaskStoreDep) -> None:
    logger.info("Received task", extra={"task_id": str(msg.task_id), "status": TaskStatus.PENDING})

    try:
        result = await execute_circuit_with_retry(msg.qc)
    except Exception as error:
        await store.record_attempt(msg.task_id, str(error))
        record = await store.get(msg.task_id)
        logger.error(f"Task {msg.task_id} failed after {record.attempts} attempts, leaving it PENDING and unacked for redelivery", extra={"task_id": str(msg.task_id)})
        raise
 
    await store.mark_completed(msg.task_id, result)
    record = await store.get(msg.task_id)
    logger.info(
        f"Task {msg.task_id} -> {record.status} (took {record.attempts} retried attempt(s)): {result}",
        extra={"task_id": str(msg.task_id)}
    )