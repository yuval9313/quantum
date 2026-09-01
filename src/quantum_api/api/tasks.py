from logging import getLogger
from typing import Annotated
from uuid import UUID, uuid4

import openqasm3
import qiskit
from fastapi import APIRouter, Body, Depends, Response, status

from common.models import TaskMessage, TaskStatus
from common.task_store import TaskStore, get_task_store
from common.tasks_broker import create_new_task

from ..data_models import TaskCreatedResponse, TaskStatusResponse

logger = getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])
TaskStoreDep = Annotated[TaskStore, Depends(get_task_store)]

MESSAGES = {
    "pending": "Task is still in progress.",
    "error": "Task not found.",
    "invalid_qasm": "Invalid QASM3 code.",
    "success": "Task submitted successfully.",
}


@router.get("/{task_id}", response_model_exclude_unset=True)
async def get_task(
    task_id: UUID, task_store: TaskStoreDep, response: Response
) -> TaskStatusResponse:
    task = await task_store.get(task_id)
    if task is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return TaskStatusResponse(status=TaskStatus.ERROR, message=MESSAGES["error"])
    if task.status != TaskStatus.COMPLETED:
        return TaskStatusResponse(status=task.status, message=MESSAGES["pending"])
    return TaskStatusResponse(status=task.status, result=task.result)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    responses={status.HTTP_400_BAD_REQUEST: {"model": TaskStatusResponse}},
    response_model_exclude_unset=True,
)
async def create_task(
    qc: Annotated[str, Body(embed=True)], task_store: TaskStoreDep, response: Response
) -> TaskStatusResponse | TaskCreatedResponse:
    try:
        qiskit.qasm3.loads(qc)
    except (openqasm3.parser.QASM3ParsingError, qiskit.qasm3.QASM3Error) as error:
        logger.warning(f"Rejected invalid QASM3 code payload: {error}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return TaskStatusResponse(
            status=TaskStatus.ERROR, message=MESSAGES["invalid_qasm"]
        )

    task_id = uuid4()
    new_task = TaskMessage(task_id=task_id, qc=qc)
    logger.info(
        "Accepted new task submission", extra={"task_id": str(task_id), "qc": qc}
    )
    await task_store.create(new_task)
    await create_new_task(new_task)
    return TaskCreatedResponse(task_id=task_id, message=MESSAGES["success"])
