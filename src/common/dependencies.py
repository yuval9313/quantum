import os
from functools import lru_cache
from .task_store import TaskStore

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/quantom")


@lru_cache()
def get_task_store() -> TaskStore:
    return TaskStore(DATABASE_URL)
