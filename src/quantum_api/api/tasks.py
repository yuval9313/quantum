from typing import Annotated
from uuid import UUID, uuid4

import openqasm3
import qiskit
from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse

from common.dependencies import get_task_store
from common.models import TaskMessage, TaskStatus
from common.task_store import TaskStore
from common.tasks_broker import create_new_task

router = APIRouter(prefix="/tasks", tags=["tasks"])
TaskStoreDep = Annotated[TaskStore, Depends(get_task_store)]

ANSWERS = {
    "pending": "Task is still in progress.",
    "error": "Task not found.",
    "invalid_qasm": "Invalid QASM3 code.",
    "success": "Task submitted successfully."
}


@router.get("/{task_id}")
async def get_task(task_id: UUID, task_store: TaskStoreDep):
    task = await task_store.get(task_id)
    if task is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"status": "error", "message": ANSWERS["error"]}
        )
    if task.status != TaskStatus.COMPLETED:
        return {"status": task.status, "message": ANSWERS["pending"]}
    return {"status": task.status, "result": task.result}


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_task(qc: Annotated[str, Body(embed=True)], task_store: TaskStoreDep):
    try:
        qiskit.qasm3.loads(qc)
    except (openqasm3.parser.QASM3ParsingError, qiskit.qasm3.QASM3Error):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": ANSWERS["invalid_qasm"]}
        )

    task_id = uuid4()
    new_task = TaskMessage(task_id=task_id, qc=qc)
    await task_store.create(new_task)
    await create_new_task(new_task)
    return {"task_id": task_id, "message": ANSWERS["success"]}
