from functools import lru_cache

from common.settings import DATABASE_URL

from .task_store import TaskStore


@lru_cache
def get_task_store() -> TaskStore:
    return TaskStore(DATABASE_URL)
