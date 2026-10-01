# Simulator V2 Phase 3 engineering report

## Delivery and scope

Branch: `feature/simulator-v2-phase3`, based on completed Phase 2 `78c18b9`.
Phase 2, Phase 1 (`6bbd35b`), and main (`729ea9c`) remain unchanged.
This phase adds bounded execution observation and inspection. It does not add a
second simulator, gates, noise, frameworks, hardware, AI behavior, or migrations.
Phase 1 and Phase 2 reports remain historical records.

Implementation commits:

- `11214bd` — bounded selected-shot tracing and API schemas.
- `2bc020e` — backend trace coverage and overhead benchmark.
- `7e290d1` — builder inspection, frontend tests, and browser verification.

A final documentation commit records this report and current usage. Use
`git log --oneline feature/simulator-v2-phase2..feature/simulator-v2-phase3`
for their exact identifiers.

## Execution architecture

The existing Phase 2 shot loop still initializes fresh quantum/classical state and
executes the same compiled operations sequentially. `TraceRecorder` observes only
requested shots. The executor evaluates a condition once, captures its actual value
before any operation can overwrite classical memory, executes or skips the existing
primitive, and optionally records a post-operation snapshot. Skipped conditions
are recorded explicitly. No extra random samples are taken for tracing.

Measurement instrumentation reuses the weights already calculated by `_measure`.
It records the actual sample and pre-sample probabilities, then the same primitive
collapses/normalizes the state and the normal executor writes its destination.
Grouped measurement samples remain in execution target order; each distribution is
conditional on earlier samples. The checkpoint state follows the complete operation.
Reset exposes its internal sample and resulting state, including whether X was
needed, without writing or clearing classical memory.

Ordinary operations reuse all existing matrices and control logic. Optional
amplitudes preserve phase information; probability-only snapshots are the default.
Snapshots are freshly serialized observations, not references to mutable shot state.
Disabled tracing allocates no recorder or quantum snapshots.

## Request and response contract

`POST /api/circuits/simulate` accepts this additional optional field:

```json
{
  "debug": {
    "enabled": true,
    "shot_numbers": [1, 2],
    "checkpoint_mode": "all",
    "include_statevector": false
  }
}
```

Defaults: disabled, shot 1, all operations, no amplitudes. Shot numbers are unique
**one-based** integers within the requested shot range, matching Phase 2 histories.
Traces are returned in execution order regardless of selection input order.
For `checkpoint_mode: "selected"`, provide unique **zero-based**
`operation_indices`. All measurement/reset/conditional operations are also retained,
including skipped operations. Selected mode cannot hide important stochastic or
classical-control events. Start/end are always included. Unknown options, invalid
modes, malformed types, invalid indices, duplicate selections, and excess budgets
return clean existing 400/422 API errors.

Normal engine results are unchanged; the typed API adds `debug: null` when disabled.
Enabled responses add this independent, versioned structure:

```text
debug:
  version: 1
  num_qubits: integer
  shot_numbering: one_based
  operation_indexing: zero_based
  operations: { "operation_index": normalized operation descriptor }
  traces:
    - shot: one-based number
      checkpoints:
        - kind: start | operation | measurement | condition | reset | end
          operation_index: zero-based index, or null for start/end
          executed: true | false | null
          quantum:
            probabilities: basis-ordered float array
            statevector: optional [real, imaginary] pairs, otherwise null
          classical: { register_name: full memory bitstring }
          condition: { actual, expected, matched }, or null
          samples:
            - qubit: integer
              destination: { register, bit }, or null for reset
              outcome: 0 | 1
              probabilities_before: [P(0), P(1)]
          outcome: final histogram key at end, otherwise null
```

The operation registry stores type, targets, quantum controls, parameters,
destinations, and classical condition once per recorded operation, shared across
shots/checkpoints. Condition expression and expected value are recoverable without
repeating the circuit inside every checkpoint. Executed conditional measurements
and resets retain their event kind plus condition evaluation. Skipped operations
have kind `condition`, `executed: false`, and no fabricated samples.

Quantum state means **this individual shot immediately after this operation**.
Start is before the first operation. End is the final circuit state before any
implicit terminal readout; that existing readout samples a copy. End also includes
the final outcome, which may differ in meaning from a quantum basis label for
classical-count circuits. This preserves Phase 2 statevector semantics. Quantum
ordering remains q(n−1)…q0; register memory remains highest bit first, in declared
register order. Unwritten memory is initialized zero, not a claim of measurement.

The existing execution version remains 2 because shot dynamics and RNG consumption
are unchanged; the independently versioned debug schema starts at 1. Supplied seeds
reproduce traces on this execution version. Debug shot selection does not change
aggregate counts, histories, or final state.

## Hard limits and performance

All limits are server-controlled; client validation is only an early convenience.

| Resource | Maximum |
| --- | ---: |
| Selected debug shots | 16 |
| Checkpoints per selected shot, including start/end | 256 |
| Checkpoints across all selected shots | 512 |
| Total checkpoint basis probability entries | 32,768 |
| Statevector snapshots when amplitudes are enabled | 64 |
| Compact serialized debug JSON | 2,000,000 bytes |
| Existing returned shot histories | 256, unchanged |
| Qubits | 10, unchanged |

These bounds compose: 10-qubit traces allow at most 32 total checkpoints because of
the basis-entry budget. Structural budgets are checked before execution; the final
byte guard rejects oversized serialized data before persistence. No silent
truncation occurs. The existing operation, shots, and total-work limits still apply.
Normal simulations do not produce debug payloads or serialize checkpoints.

A diagnostic benchmark loads the unchanged Phase 2 engine from Git and checks
exact normal-result equality before timing nine alternating runs per circuit.
Measured medians in this environment:

| Circuit (2,048 shots, 4 qubits) | Phase 2 | Debug disabled | One traced shot | Disabled/baseline |
| --- | ---: | ---: | ---: | ---: |
| Unitary | 0.071331 s | 0.070659 s | 0.070278 s | 0.991 |
| Feed-forward | 0.033166 s | 0.033617 s | 0.033499 s | 1.014 |

These measurements show no material disabled-mode regression in these cases;
they are not a universal latency guarantee or a flaky timing test requirement.

## Frontend and persistence

The builder adds opt-in debug controls, selected shot numbers, all/selected
checkpoint mode, selected operation numbers, and optional amplitudes. UI operation
numbers are one-based and converted to API indices. Invalid budgets and indices
produce useful pre-submit errors. The existing circuit interaction is preserved.

The result inspector offers a shot selector, previous/next navigation, checkpoint
indicator, selectable timeline, and matching circuit-column highlight. It labels
executed/skipped operations, quantum controls, classical condition actual/expected
values, measurement/reset samples, classical memory, and checkpoint quantum state.
A shared quantum table reuses the final-state presentation and paginates at 32 basis
rows. This avoids rendering 1,024 rows at once. Debug UI is absent for normal runs.
Displayed events come from the response operation registry, not a reconstructed
frontend simulation. Aggregate counts and last-shot outputs remain separate.

Debug traces are **transient response metadata** and are not added to persisted
SimulationResult JSON. Request configuration can naturally remain in saved circuit
JSON. Authenticated Circuit → CircuitVersion → SimulationRun → SimulationResult
transactions, ownership, retrieval, and existing bounded shot-history persistence
are unchanged. No database migration, schema rewrite, or authentication change.

## Changed files

- `backend/app/services/simulators/tracing.py`: validation, budgets, snapshots, registry.
- `backend/app/services/simulators/engine.py`: optional hooks in the existing executor.
- `backend/app/schemas/circuit.py`: typed additive debug request/result schemas.
- `backend/tests/test_simulator_v2_phase3.py`: 73 engine/API/persistence cases.
- `backend/scripts/benchmark_trace_overhead.py`: reproducible baseline comparison.
- `frontend/src/lib/api.ts`: additive request/result typing.
- `frontend/src/lib/simulation-trace.ts`: trace model, validation, labels/navigation.
- `frontend/src/components/circuit-builder/DebugControls.tsx`: request controls.
- `frontend/src/components/circuit-builder/ExecutionTrace.tsx`: selected-shot inspector.
- `frontend/src/components/circuit-builder/QuantumStateTable.tsx`: shared paginated view.
- `frontend/src/components/circuit-builder/CircuitBuilder.tsx`: integration/highlights.
- `frontend/tests/simulation-trace.test.cjs`: seven helper/rendering tests.
- `frontend/tests/browser/simulator-v2-phase3.cjs`: real API browser verification.
- `docs/SIMULATOR_V2.md`, this report, `README.md`: current capabilities and usage.

## Verification results

- Full PostgreSQL-backed backend suite: **431 passed, zero skipped**; one upstream
  Starlette/AnyIO warning. Includes all existing Phase 1/2 tests unchanged.
- Phase 3 backend cases cover disabled parity/no allocation, selected and late shots,
  every checkpoint kind, H probabilities and phase amplitudes, collapse, classical
  writes, both condition branches, condition-before-overwrite, sequential opposite
  measurements, grouped conditional samples, reset, controlled/parameterized gates,
  snapshot independence, normalization, every bound and malformed API inputs,
  guest/authenticated persistence, and transient trace storage.
- Frontend: **six test files passed**, including seven Phase 3 tests for controls,
  validation, navigation bounds, timelines, skipped operations, condition/measurement/
  reset rendering, quantum/classical state, and pagination.
- Ruff, ESLint, TypeScript, production build, and whitespace checks passed.
- Phase 1 browser: all 21 palette operations, serialization, angles, Bell/reset,
  result labels, mobile layout passed.
- Phase 2 browser: Bell, feed-forward, opposite sequential measurements, reset memory,
  seeds, registers/conditions, bounded histories, validation, mobile layout passed.
- Phase 3 browser: real H/collapse, both conditional branches, executed/skipped labels,
  reset retaining c0, shot selection including shot 32, navigation, timeline/circuit
  highlight, selected mode, amplitudes, disabled parity, validation, mobile layout
  passed. No mocked simulation responses. The conditional inspector screenshot was
  also visually inspected. Browser navigation is automated, not a separate claim of
  human manual interaction.

Exact verification commands, from repository root unless noted:

```sh
TEST_DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check backend/.venv/bin/python -m pytest backend/tests -q
backend/.venv/bin/ruff check backend/app/
git diff --check
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/benchmark_trace_overhead.py
# From frontend/:
npm test
npm run lint
npm run typecheck
npm run build
# Repository root, with the production frontend and API running:
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2.cjs
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase2.cjs
SIMULATOR_SCREENSHOT=/tmp/simulator-v2-phase3.png NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase3.cjs
```

Local server commands used (separate terminals, existing isolated migrated test DB):

```sh
DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
# From frontend/:
PORT=13002 npm run start
```

## Limitations and recommended Phase 4

This is inspection of completed runs, not pausing/resuming a live engine or editing
a past quantum state. Selected shots must be requested before execution; there is
no retrospective trace endpoint. Default probabilities omit phase unless amplitudes
are enabled. Selected mode can omit ordinary gates, but never measurement/reset/
conditional checkpoints. Internal terminal-readout substeps are not traced.
Full pre-operation statevectors are not duplicated; the preceding checkpoint and
actual pre-sample probabilities supply the relevant context. Large circuits may
need fewer selected operations/shots to fit budgets. Traces are not retrievable
from saved history. Existing Phase 2 simulation limitations remain.

Recommended Phase 4: bounded trace-driven teaching diagnostics, consuming the
versioned operation registry and selected checkpoint sequence. Start with verified
explanations for measurement collapse, skipped classical conditions, and reset
versus classical memory, with references to exact shot/operation identifiers and
numerical evidence. This architecture now provides that data without rerunning a
second simulator. Any future AI integration should use explicitly selected,
bounded context and be tested against these deterministic traces; no AI service
or tutor behavior was changed in Phase 3.
