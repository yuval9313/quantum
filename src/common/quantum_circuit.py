from qiskit import QuantumCircuit, transpile 
from qiskit_aer import AerSimulator 

NUM_SHOTS = 1024 


def create_basic_quantum_circuit() -> QuantumCircuit: 
    qc = QuantumCircuit(2, 2) 
    qc.h(0)                     
    qc.cx(0, 1)                 
    qc.measure([0, 1], [0, 1])  
    return qc 


def execute_circuit(qc: QuantumCircuit) -> dict: 
    simulator = AerSimulator() 
    qc_transpiled = transpile(qc, simulator) 
    job = simulator.run(qc_transpiled, shots=NUM_SHOTS) 
    result = job.result() 
    return result.get_counts() 