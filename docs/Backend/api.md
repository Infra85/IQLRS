# API Reference


#### `POST /api/circuits/simulate`
Simulate a quantum circuit.

**Request:**
```json
{
  "gates": [
    { "type": "H", "qubit": 0 },
    { "type": "CNOT", "control": 0, "target": 1 }
  ],
  "num_qubits": 2,
  "shots": 1024,
  "backend": "qiskit"
}
```

**Response:**
```json
{
  "counts": { "00": 512, "11": 512 },
  "statevector": [...],
  "circuit_diagram": "..."
}
```

### Code Execution

#### `POST /api/code/execute`
Execute user-submitted quantum code.

**Request:**
```json
{
  "code": "from qiskit import QuantumCircuit...",
  "framework": "qiskit"
}
```

### AI Tutor

#### `POST /api/ai/chat`
Send a message to the AI tutor.

**Request:**
```json
{
  "message": "Explain quantum entanglement",
  "context": { "current_module": "entanglement", "circuit": null }
}
```

#### `POST /api/ai/debug`
Analyze code for errors.

**Request:**
```json
{
  "code": "...",
  "error": "TypeError: ...",
  "framework": "qiskit"
}
```
