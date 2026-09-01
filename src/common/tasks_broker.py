import os
from logging import getLogger
from uuid import uuid4

from faststream.redis import RedisBroker, StreamSub

from common.models import TaskMessage

logger = getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
broker = RedisBroker(url=REDIS_URL)

consumer_id = os.getenv("HOSTNAME", str(uuid4()))
tasks_stream = StreamSub("tasks", group="task-workers", consumer=consumer_id)
publisher = broker.publisher(stream=tasks_stream)


async def create_new_task(task: TaskMessage) -> None:
    logger.info(f"Publishing new task {task.task_id}")
    await publisher.publish(task)
    
