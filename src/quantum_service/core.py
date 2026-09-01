import asyncio
import logging

from qiskit import QuantumCircuit, transpile, qasm3
from qiskit_aer import AerSimulator

from faststream import Context
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common.quantum_circuit import execute_circuit

NUM_SHOTS = 1024 

@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(Context("logger"), logging.WARNING),
    reraise=True,
)
async def execute_circuit_with_retry(qc: str) -> dict:
    encoded_circuit = qasm3.loads(qc)
    return await asyncio.to_thread(execute_circuit, encoded_circuit)


def execute_circuit(qc: QuantumCircuit) -> dict: 
    simulator = AerSimulator() 
    qc_transpiled = transpile(qc, simulator) 
    job = simulator.run(qc_transpiled, shots=NUM_SHOTS) 
    result = job.result() 
    return result.get_counts() 