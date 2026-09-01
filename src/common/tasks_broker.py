from logging import getLogger

from faststream.redis import RedisBroker, StreamSub

from common.models import TaskMessage
from common.settings import CONSUMER_ID, REDIS_URL

logger = getLogger(__name__)

broker = RedisBroker(url=REDIS_URL)

tasks_stream = StreamSub("tasks", group="task-workers", consumer=CONSUMER_ID)
publisher = broker.publisher(stream=tasks_stream)


async def create_new_task(task: TaskMessage) -> None:
    logger.info(f"Publishing new task {task.task_id}")
    await publisher.publish(task)
