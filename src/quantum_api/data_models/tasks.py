from uuid import UUID

from pydantic import BaseModel, Field

from common.models import TaskStatus


class TaskStatusResponse(BaseModel):
    status: TaskStatus
    message: str | None = Field(default=None)
    result: dict | None = Field(default_factory=dict)


class TaskCreatedResponse(BaseModel):
    task_id: UUID
    message: str
