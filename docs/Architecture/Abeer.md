# Abeer

Abeer handles the actual quantum computing engine. The roadmap specifically assigns code editing, multi-backend simulation and sandboxed execution here.

Abeer should build
1. Monaco Code Editor

Support:

Qiskit
PennyLane
Cirq

Example:

from qiskit import QuantumCircuit

qc = QuantumCircuit(2)

qc.h(0)
qc.cx(0, 1)

qc.measure_all()
2. Simulation API

Build:

POST /api/circuits/simulate

Input:

{
  "circuit": {...},
  "backend": "qiskit_aer",
  "shots": 1000
}

Output:

{
  "measurements": {
    "00": 498,
    "11": 502
  },
  "probabilities": {
    "00": 0.498,
    "11": 0.502
  },
  "state_vector": [...]
}
3. Multi-backend architecture
             Simulator API
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
     Qiskit    PennyLane     Cirq
       Aer
4. Code execution

Build sandboxed execution.

P2's deliverable

A working pipeline:

Circuit / Code
      ↓
FastAPI
      ↓
Quantum Simulator
      ↓
Results
      ↓
Frontend