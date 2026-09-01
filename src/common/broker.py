from common.models import TaskMessage
from common.dependencies import get_task_store
import os
from faststream.redis import RedisBroker, StreamSub
from loguru import logger

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
broker = RedisBroker(url=REDIS_URL)

tasks_stream = StreamSub("tasks", group="task-workers", consumer="1")


@broker.publisher(stream=tasks_stream)
async def create_new_task(task: TaskMessage) -> TaskMessage:
    logger.info(f"Publishing new task {task.task_id}")
    return task
    
