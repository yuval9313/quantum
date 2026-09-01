import asyncio
import logging

import qiskit
from faststream import Context
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common.quantum_circuit import execute_circuit


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(Context("logger"), logging.WARNING),
    reraise=True,
)
async def execute_circuit_with_retry(qc: str) -> dict:
    encoded_circuit = qiskit.qasm3.loads(qc)
    return await asyncio.to_thread(execute_circuit, encoded_circuit)

