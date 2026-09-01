from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field as ModelField
from sqlmodel import SQLModel, Field as SQLField
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, DateTime


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class TaskMessage(BaseModel):
    task_id: UUID = ModelField(default_factory=uuid4)
    qc: str
    created_at: datetime = ModelField(default_factory=lambda: datetime.now(timezone.utc))


class TaskRecord(SQLModel, table=True):
    __tablename__ = "tasks"

    task_id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    status: TaskStatus = SQLField(default=TaskStatus.PENDING, index=True)
    qc: str
    created_at: datetime = SQLField(sa_type=DateTime(timezone=True))
    result: dict = SQLField(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    updated_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
    attempts: int = SQLField(default=0)
    last_error: Optional[str] = SQLField(default=None)