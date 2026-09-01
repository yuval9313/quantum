from sqlalchemy.ext.asyncio import create_async_engine
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine

from .models import TaskMessage, TaskRecord, TaskStatus


class TaskStore:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def create_db_and_tables(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def close(self) -> None:
        await self._engine.dispose()
 
    async def create(self, msg: TaskMessage) -> None:
        async with self._session_factory() as session:
            record = TaskRecord(
                task_id=msg.task_id,
                qc=msg.qc,
                created_at=msg.created_at,
            )
            session.add(record)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
 
    async def record_attempt(self, task_id: UUID, error: Optional[str] = None) -> None:
        async with self._session_factory() as session:
            record = await session.get(TaskRecord, task_id)
            if record is None:
                return
            record.attempts += 1
            record.last_error = error
            record.updated_at = datetime.now(timezone.utc)
            session.add(record)
            await session.commit()
 
    async def mark_completed(self, task_id: UUID) -> None:
        async with self._session_factory() as session:
            record = await session.get(TaskRecord, task_id)
            if record is None:
                return
            record.status = TaskStatus.COMPLETED
            record.updated_at = datetime.now(timezone.utc)
            session.add(record)
            await session.commit()
 
    async def get(self, task_id: UUID) -> Optional[TaskRecord]:
        async with self._session_factory() as session:
            return await session.get(TaskRecord, task_id)
 