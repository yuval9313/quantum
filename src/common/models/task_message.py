from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel
from pydantic import Field as ModelField


class TaskMessage(BaseModel):
    task_id: UUID = ModelField(default_factory=uuid4)
    qc: str
    created_at: datetime = ModelField(default_factory=lambda: datetime.now(UTC))
