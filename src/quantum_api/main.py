from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.dependencies import get_task_store
from common.tasks_broker import broker

from .api import tasks_router
from .api.hidden import router as internal


@asynccontextmanager
async def lifespan(app: FastAPI):
    task_store = get_task_store()
    await task_store.create_db_and_tables()
    await broker.start()
    yield
    await broker.stop()
    await task_store.close()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(tasks_router)
    app.include_router(internal)
    return app


app = create_app()
