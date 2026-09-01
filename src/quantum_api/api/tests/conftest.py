import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ..tasks import router as tasks_router


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(tasks_router)
    return app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
