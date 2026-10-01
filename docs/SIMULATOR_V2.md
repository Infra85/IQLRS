# Simulator V2 — Phase 1

The circuit builder sends ordered `Gate[]` JSON through `simulateCircuit` to
`POST /api/circuits/simulate`. Pydantic checks payload shape; the engine validates
operations, resolves matrices, and executes them. `CircuitResult` returns samples,
amplitudes, explicit measurement records, and execution metadata. Signed-in runs
retain the existing Circuit → CircuitVersion → SimulationRun → SimulationResult
transaction. Guests receive results without persistence.

## Operations and payloads

Existing `type`, `qubit`, `control`, and `target` fields remain supported. Gate names
are case-insensitive; CX aliases CNOT, and ID/IDENTITY/HADAMARD remain aliases.

- Single-qubit: I, H, X, Y, Z, S, T, SDG (S†), TDG (T†).
- Rotations: RX, RY, RZ with required numeric `params.theta` in radians.
- Two-qubit: SWAP and controlled X/Y/Z/H/rotations (CNOT/CX, CY, CZ, CH,
  CRX, CRY, CRZ).
- Nonunitary: MEASURE on one qubit, MEASURE_ALL, RESET on one qubit.

```json
{
  "num_qubits": 3,
  "shots": 1024,
  "backend": "qiskit",
  "gates": [
    {"type": "RY", "qubit": 0, "params": {"theta": 1.5707963267948966}},
    {"type": "CRX", "control": 0, "target": 2, "params": {"theta": 3.141592653589793}},
    {"type": "SWAP", "targets": [0, 1]},
    {"type": "MEASURE", "qubit": 2},
    {"type": "RESET", "qubit": 2},
    {"type": "MEASURE_ALL"}
  ]
}
```

The optional `targets` and `controls` arrays generalize legacy indices. For example,
`{"type":"RY","targets":[2],"controls":[0,1],"params":{"theta":0.5}}`
executes RY only when **all** controls are 1. All single-qubit matrices, including
S/T and inverses, can use controls; corresponding C-prefixed names also work.
Targets currently contain one qubit except SWAP (two). SWAP also accepts the
builder's `control`/`target` pair as two symmetric endpoints. Do not mix array
indices with legacy index fields. Indices must be distinct integers in range.

The engine compiles matrices once, then uses one in-place amplitude-pair primitive
for both ordinary and controlled operators. SWAP exchanges amplitude pairs directly.
The historical backend name `qiskit` is retained; it now consistently dispatches to
the shared Python engine, independent of installed native packages. Metadata names
the actual engine `statevector-v2`. Cirq/PennyLane are not execution backends here.

## Ordering

q0 is the least-significant bit. Amplitude index `i` corresponds to the binary
encoding of `i`; bitstrings read **q(n−1)…q0**. X(q0) on three qubits yields `001`,
not `100`. The builder draws q0 at the top; this does not reverse result labels.
Explicit measurement records list qubits in descending order, matching their bits.

## Measurement, reset, and results

MEASURE samples Born probabilities, discards incompatible amplitudes, and
renormalizes the remaining state. MEASURE_ALL sequentially measures every qubit,
preserving correlations. Each shot restarts from the initial all-zero state.
A deterministic unitary prefix is computed once and reused across trajectories.
Operations following a measurement see its collapsed state.

RESET internally measures its qubit and applies X for outcome 1. Its target ends
in |0⟩; entangled partners retain their sampled **conditional** state. Reset of a
Bell pair does not restore its partner to a superposition. Internal reset outcomes
are not exposed as explicit classical measurement records.

Response fields:

- `counts`: final computational-basis samples across all shots, including circuits
  with no explicit measurement. This preserves the old contract. This terminal
  readout does not alter the returned statevector.
- `statevector`: `[real, imaginary]` amplitudes after the circuit. For unitary
  circuits this is the exact pure state; with measurement/reset this is the
  **last shot's conditional state**, not an ensemble average.
- `measurements`: last-shot explicit records: zero-based `operation`, descending
  `qubits`, and `bits`. Later gates may change the state after these observations.
- `measurement_counts`: histograms keyed by zero-based operation index; each
  histogram aggregates that explicit measurement across all shots.
- `metadata`: engine, shots, bit order, and `statevector_scope` (`unitary` or
  `last_shot`).
- `simulation_id`, `circuit_diagram`: existing fields.

Exact state probabilities are derived as real² + imaginary²; they are not duplicated
in the response. The UI labels these separately from empirical shot counts and
shows explicit measurements separately from the final readout. The existing
persisted `probabilities` column continues to hold final count frequencies.
Additional records and metadata are saved in the existing state-vector JSON beside
`amplitudes` and returned by the run retrieval endpoint. No schema migration or
historical data rewrite is needed; older rows remain readable.

## Builder and validation

Choose a gate and wire, or drag a gate. Linked operations select two wires. The
angle editor accepts finite decimal/scientific radians and simple expressions such
as `pi`, `-pi/2`, `3*pi/4`, and `π/2`, without evaluating code. Existing rotation
angles can be edited below the palette; edits commit on blur, and invalid edits
report an error and retain the previous angle. API payloads always contain numbers,
not expressions. The API rejects missing/nonfinite parameters, invalid indices,
duplicate indices, unsupported operations, and malformed payloads via 400/422
responses. The builder checks circuit indices and parameters before submitting.

## Limits

- 1–10 qubits, at most 500 operations; API shots 1–100,000, builder shots 1–8,192.
- Stochastic circuits are bounded by
  `shots × (operations from first measurement/reset + 1) × 2^qubits ≤ 20,000,000`.
  Requests above that budget return a clear error; reduce shots/qubits/operations.
- Pure-state trajectories only: no density matrices, noise, classical feedback,
  symbolic parameter bindings, hardware execution, or saved per-shot histories.
- Explicit histograms are per-operation marginals, not joint measurement histories.
- The builder exposes single-control gates; multiple controls and inverse phase
  gates are available through the API/engine.
- Sampling varies between runs. Tests inject a seeded random generator internally;
  no public seed API is promised.

Phase 2 should add classical registers and conditional execution, with a defined
joint-shot result model, before adding noise/density-matrix simulation.

## Verification commands

From the repository root, with an isolated PostgreSQL database available:

```sh
TEST_DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check backend/.venv/bin/python -m pytest backend/tests -q
backend/.venv/bin/ruff check backend/app/
git diff --check
cd frontend
npm test
npm run lint
npm run typecheck
npm run build
```

The browser regression is opt-in and requires Playwright plus Chrome. It runs
against the production build and a real API, not mocked simulation responses.
The following were used during verification (server commands run in separate
terminals; the default production rewrite targets port 8000):

```sh
# Repository root; initialize only a dedicated, disposable test database.
initdb -D /tmp/iqlrs-v2-pg -A trust --no-locale
pg_ctl -D /tmp/iqlrs-v2-pg -l /tmp/iqlrs-v2-pg.log -o '-h 127.0.0.1 -p 55439 -k /tmp' start
createdb -h 127.0.0.1 -p 55439 -E UTF8 -T template0 iqlrs_check
DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check PYTHONPATH=backend backend/.venv/bin/python -m app.migrate
DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
# From frontend/ in a separate terminal:
PORT=13002 npm run start
# From the repository root in another terminal:
npm install --prefix /tmp/iqlrs-browser-check playwright
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2.cjs
```

Browser overrides: `CHROME_PATH` selects the Chrome executable, `BUILDER_URL`
selects the frontend origin. The script uses a new guest context and checks all
21 palette operations, angle editing/validation, serialization, actual API
responses, Bell collapse/reset, result labels, and mobile horizontal overflow.
