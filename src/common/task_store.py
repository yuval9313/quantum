from datetime import UTC, datetime
from logging import getLogger
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import TaskMessage, TaskRecord, TaskStatus

logger = getLogger(__name__)


class TaskStore:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

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
                logger.warning(f"Task {msg.task_id} already exists.")
                await session.rollback()

    async def record_attempt(self, task_id: UUID, error: str | None = None) -> None:
        async with self._session_factory() as session:
            record = await session.get(TaskRecord, task_id)
            if record is None:
                logger.warning(f"Attempted to update non-existent task {task_id}")
                return
            record.attempts += 1
            record.last_error = error
            record.updated_at = datetime.now(UTC)
            session.add(record)
            await session.commit()

    async def mark_completed(self, task_id: UUID, result: dict) -> None:
        async with self._session_factory() as session:
            record = await session.get(TaskRecord, task_id)
            if record is None:
                logger.warning(
                    f"Attempted to mark non-existent task {task_id} as completed"
                )
                return
            record.status = TaskStatus.COMPLETED
            record.updated_at = datetime.now(UTC)
            record.result = result
            session.add(record)
            await session.commit()

    async def get(self, task_id: UUID) -> TaskRecord | None:
        async with self._session_factory() as session:
            return await session.get(TaskRecord, task_id)
