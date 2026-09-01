from faststream import FastStream
from common.broker import broker, tasks_stream
from types import Annotated
from faststream import Logger
from common.models import TaskMessage
from common.task_repo import TaskStore, TaskStatus
from fast_depends import Depends
from common.dependencies import get_task_store

TaskStoreDep = Annotated[TaskStore, Depends(get_task_store)]
app = FastStream(broker)


@broker.subscriber(stream=tasks_stream)
async def handle_task(msg: TaskMessage, logger: Logger, store: TaskStoreDep) -> None:
    await store.create(msg)
    logger.info(f"Received task {msg.task_id} (status={TaskStatus.PENDING})")
 
    try:
        result = await process_with_retry(msg.task_id, msg.payload)
    except TransientError:
        record = await store.get(msg.task_id)
        logger.error(
            f"Task {msg.task_id} failed after {record.attempts} attempts, "
            "leaving it PENDING and unacked for redelivery"
        )
        raise
 
    await store.mark_completed(msg.task_id)
    record = await store.get(msg.task_id)
    logger.info(
        f"Task {msg.task_id} -> {record.status} "
        f"(took {record.attempts} retried attempt(s)): {result}"
    )