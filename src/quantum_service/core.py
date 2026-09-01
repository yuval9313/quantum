import asyncio
import logging

from faststream import Context
from qiskit import QuantumCircuit, qasm3, transpile
from qiskit_aer import AerError, AerSimulator
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .constants import MAX_RETRIES

NUM_SHOTS = 1024
RETRY_EXCEPTIONS = (MemoryError, AerError)


async def execute_circuit(qc: str) -> dict:
    encoded_circuit = qasm3.loads(qc)
    return await asyncio.to_thread(_execute_circuit_with_retry, encoded_circuit)


@retry(
    retry=retry_if_exception_type(RETRY_EXCEPTIONS),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(Context("logger"), logging.WARNING),
    reraise=True,
)
def _execute_circuit_with_retry(qc: QuantumCircuit) -> dict:
    simulator = AerSimulator()
    qc_transpiled = transpile(qc, simulator)
    job = simulator.run(qc_transpiled, shots=NUM_SHOTS)
    result = job.result()
    return result.get_counts()
