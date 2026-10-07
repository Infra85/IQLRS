# Simulator V2 Phase 1 engineering report

Implemented on `feature/simulator-v2-phase1`, branched from main at `729ea9c`.

## Changes

| Files | Purpose |
| --- | --- |
| `backend/app/services/simulators/engine.py` | Validated operations, reusable controlled matrix primitive, rotations/phase/SWAP, stochastic measurement/reset, ordering and execution metadata |
| `backend/app/services/simulators/qiskit_runner.py` | Preserve runner/API entry point while consistently using the shared engine |
| `backend/app/schemas/circuit.py` | Add optional numeric params, controls/targets arrays, measurement records/histograms/metadata; strict integer indices |
| `backend/app/api/circuits.py` | Persist additional result fields inside existing JSON |
| `backend/tests/test_simulator_v2.py` | Analytical, stochastic, normalization, validation, API, guest, and authenticated persistence tests |
| `backend/tests/test_circuits.py` | Keep unsupported-gate regression using an actually unsupported gate; missing rotation parameters covered in V2 tests |
| `frontend/src/components/circuit-builder/CircuitBuilder.tsx` | Expanded palette, angle editors, linked gates, measurement/reset symbols, clearly labeled results |
| `frontend/src/components/circuit-builder/edit-circuit.ts` | Shared operation construction, angle parsing, validation, linked-gate movement |
| `frontend/src/lib/api.ts` | Additive TypeScript gate/result fields |
| `frontend/tests/circuit-edit.test.cjs` | Parsing, operation serialization, linked movement, validation regressions |
| `frontend/tests/browser/simulator-v2.cjs` | Real production-builder/API browser regression |
| `README.md`, `docs/Backend/api.md`, `docs/SIMULATOR_V2.md` | Accurate capabilities, API semantics, ordering, limits, reproducible verification commands |
| `docs/SIMULATOR_V2_PHASE1_REPORT.md` | This engineering report |

New gates: RX/RY/RZ, S/T and API inverses SDG/TDG, SWAP, CY/CZ/CH,
CRX/CRY/CRZ. CNOT/CX and I/H/X/Y/Z remain supported. Controls are reusable
across single-qubit matrices, including multiple controls in the API. Measurement
and reset execute as probabilistic, normalized state trajectories.

No database schema changes or migration files. Existing JSON columns retain the
Circuit → CircuitVersion → SimulationRun → SimulationResult persistence chain.
The legacy `qiskit` backend name now always uses the shared statevector engine,
avoiding divergent behavior based on optional native package installation.

## Verified results

- Full backend suite with isolated PostgreSQL: **226 passed, zero skipped**.
- Frontend test suite: **all four test files passed**.
- Backend Ruff and frontend ESLint: passed.
- Frontend TypeScript check and production build: passed.
- Chrome against production frontend plus real local API: **all 21 palette
  operations passed**, including numeric serialization, invalid angle rejection,
  editing existing angles, Bell measurement/reset, result labels, and mobile width.
- `git diff --check`: passed.

The backend suite includes independent analytical expectations for rotation angles
0, π, ±π/2, and a decimal angle on both basis states; phase gates on basis and
superposition states; nonadjacent/reversed SWAP; controlled operations; seeded Bell
sampling and collapse; entangled reset; random unitary inverse/normalization
checks; strict validation; and authenticated result retrieval with all four
persistence records present. No existing tests were removed or weakened.

Exact test, build, lint, database setup, and browser execution commands are recorded
in [Simulator V2 verification commands](SIMULATOR_V2.md#verification-commands).

One upstream Starlette/AnyIO deprecation warning remains in backend tests; Next.js
also reports that `next lint` will be removed in its next major version.

## Limits and next step

Ten-qubit limit retained. Numeric parameters only. Multiple controls and phase
inverses are API features; the builder offers single controls. Stochastic execution
has a documented work budget. Its returned statevector is the last shot's
conditional pure state; counts aggregate all shots. Per-operation measurement
histograms do not retain joint per-shot histories. No noise model, density matrix,
classical feedback, or hardware execution.

Recommended Phase 2: classical registers and conditional execution, with a clear
joint-shot result model, then noise/density-matrix support.
