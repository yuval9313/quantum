from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"
