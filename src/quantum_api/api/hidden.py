import qiskit
from fastapi import APIRouter
from common.quantum_circuit import create_basic_quantum_circuit

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


@router.get("/create-qc")
async def create_qc() -> str:
    qc = create_basic_quantum_circuit()
    return qiskit.qasm3.dumps(qc)