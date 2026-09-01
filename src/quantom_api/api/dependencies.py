
from functools import lru_cache
from common.task_repo import TaskStore


@lru_cache()
def get_task_store() -> TaskStore:
    return TaskStore("postgresql+asyncpg://postgres:postgres@localhost:5432/quantom")
