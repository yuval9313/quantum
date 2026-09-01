from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.tasks_broker import broker
from common.task_store import get_task_store

from .api import tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    task_store = get_task_store()
    await task_store.create_db_and_tables()
    await broker.start()
    yield
    await broker.stop()
    await task_store.close()


app = FastAPI(lifespan=lifespan)

app.include_router(tasks_router)
