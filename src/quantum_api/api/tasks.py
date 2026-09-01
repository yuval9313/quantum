from faststream.asgi.response import JSONResponse
import openqasm3
from fastapi import Body, status
import qiskit
from common.tasks_broker import create_new_task
from common.models import TaskMessage, TaskStatus
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID, uuid4
from typing import Annotated

from common.dependencies import get_task_store
from common.task_store import TaskStore

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
            data={"status": "error", "message": ANSWERS["error"]}
        )
    if task.status != TaskStatus.COMPLETED:
        return {"status": task.status, "message": ANSWERS["pending"]}
    return {"status": task.status, "result": task.result}


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_task(qc: Annotated[str, Body(embed=True)], task_store: TaskStoreDep):
    try:
        qiskit.qasm3.loads(qc)
    except openqasm3.parser.QASM3ParsingError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            data={"status": "error", "message": ANSWERS["invalid_qasm"]}
        )

    task_id = uuid4()
    new_task = TaskMessage(task_id=task_id, qc=qc)
    await task_store.create(new_task)
    await create_new_task(new_task)
    return {"task_id": task_id, "message": ANSWERS["success"]}
