from common.tasks_broker import create_new_task
from common.models import TaskMessage, TaskStatus
from fastapi import APIRouter, Depends
from uuid import UUID, uuid4
from typing import Annotated

from common.dependencies import get_task_store
from common.task_repo import TaskStore

router = APIRouter()
TaskStoreDep = Annotated[TaskStore, Depends(get_task_store)]

ANSWERS = {
    TaskStatus.PENDING: "Task is still in progress.",
    "error": "Task not found.",
}


@router.get("/{task_id}")
async def get_task(task_id: UUID, task_store: TaskStoreDep):
    task = await task_store.get(task_id)
    if task is None:
        return {"status": "error", "message": ANSWERS["error"]}
    if task.status != TaskStatus.COMPLETED:
        return {"status": task.status, "message": ANSWERS[task.status]}
    return {"status": task.status, "result": task.result}


@router.post("")
async def create_task(qc: str, task_store: TaskStoreDep):
    task_id = uuid4()
    await task_store.create(TaskMessage(task_id=task_id, qc=qc))
    await create_new_task(TaskMessage(task_id=task_id, qc=qc))
    return {"task_id": task_id, "message": "Task submitted successfully."}
