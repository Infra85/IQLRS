# Simulator V2 Phase 2 engineering report

Implemented on `feature/simulator-v2-phase2`, starting from the clean Phase 1 tip
`6bbd35b`. `main` remains at `729ea9c`; Phase 1 and its report remain unchanged.

## Commits

- `693ffef` — `feat(simulator): add classical state and sequential per-shot execution`
- `82aeeb5` — `test(simulator): cover phase 2 classical control and joint shot results`
- `a1fe341` — `feat(builder): integrate classical control and bounded shot history`
- Documentation commit — `docs(simulator): document phase 2 execution and verification`
  (contains this report; see branch history for its hash).

## Files changed

| File | Change |
| --- | --- |
| `backend/app/services/simulators/classical.py` | Register/reference/condition validation, equality evaluation, memory snapshots and measured-bit projection |
| `backend/app/services/simulators/engine.py` | Sequential independent shots; classical measurement writes; generic condition wrapper; seed, histories, joint counts and limits |
| `backend/app/schemas/circuit.py` | Typed classical registers/references/conditions; seed and shot-record bounds; additive result fields |
| `backend/app/api/circuits.py` | Persist Phase 2 JSON fields and populate the existing classical-bit count column |
| `backend/tests/test_simulator_v2_phase2.py` | 132 new backend test cases covering semantics, validation, invariants, API and persistence |
| `frontend/src/lib/api.ts` | Request/result TypeScript extensions |
| `frontend/src/components/circuit-builder/CircuitBuilder.tsx` | Connect register configuration, mapped measurement placement, seeds, shot history and IF markers |
| `frontend/src/components/circuit-builder/ClassicalControls.tsx` | Named register editor, destination pickers and per-operation bit/register equality controls |
| `frontend/src/components/circuit-builder/ClassicalResults.tsx` | Last-shot classical memory and bounded expandable measurement histories |
| `frontend/src/components/circuit-builder/classical-circuit.ts` | Mapping defaults, safe destination editing, labels and frontend validation |
| `frontend/tests/classical-circuit.test.cjs` | Defaults, serialization, movement, conditions, validation and incomplete mapping regressions |
| `frontend/tests/browser/simulator-v2-phase2.cjs` | Real browser/API execution of representative circuits and editing flows |
| `docs/SIMULATOR_V2.md` | Current execution model, request/result contract, compatibility, ordering, limits and reproduction commands |
| `docs/Backend/api.md` | Reference to the extended simulation contract |
| `README.md` | Updated simulator capabilities |
| `docs/SIMULATOR_V2_PHASE2_REPORT.md` | This report |

No authentication, dashboard, tutor, narration, deployment, curriculum, alternate
runtime, hardware or collaboration implementation was changed.

## Architecture and semantics

Phase 1 matrices, quantum-control primitive, SWAP, measurement collapse and reset
are reused. Validation compiles operations once; each shot then initializes its own
|0…0⟩ statevector, zero-valued classical memory and measurement history, and runs the
complete operation sequence. There is no state shared between shots or simulation
once followed by manufactured counts.

Registers are ordered `{name, size}` definitions: up to eight unique identifiers
and 32 total bits. A classical reference is `{register, bit}`. Within a register,
bit zero is least significant. Measurement destinations map positionally to target
qubits, must exist, and must be distinct within one operation. Writes across
successive operations may overwrite memory; history retains the original events.

A condition is `{register, bit?, operator: "eq", value}`. Omitting `bit` compares the
whole register integer. The same wrapper evaluates every operation before dispatch;
quantum controls subsequently act on amplitudes independently of that classical
condition. Conditions can inspect initialized zero bits. Conditional measurement
and reset also use the wrapper. Reset preserves classical memory.

MEASURE and MEASURE_ALL sample and collapse during execution, then immediately
write classical bits. Later operations see both the collapsed quantum state and
updated memory. Terminal quantum readout uses the same measurement primitive on
a copy, preserving the exposed statevector.

`seed` selects a request-local RNG; identical seeded requests reproduce execution
results without altering global randomness. Without a seed runs remain stochastic.
Changing the history-return limit does not change sampling.

## API, results, and compatibility

The existing `POST /api/circuits/simulate` accepts optional `classical_registers`,
`seed`, `shot_record_limit`, and gate `destinations`/`condition`. Existing gate and
qubit fields are unchanged. Shape errors use 422; engine semantic errors use 400.

For explicit classical circuits with measurements, `counts` is the joint final
measured-memory histogram. Register declaration order, then descending bit index,
determines `classical_bit_order`. Unmapped bits are excluded. A mapped bit with no
executed write is labeled `x`; unwritten memory still has initialized value zero.

Legacy payloads retain Phase 1 final quantum-readout counts and last-measurement
shape. They receive an internal `c` register with q[i]→c[i] mappings. New classical
features opt into explicit mappings; every measurement then requires destinations.
Without explicit register declarations, references can use implicit `c` memory.
Circuits without any measurement preserve quantum-readout behavior.

New results include effective registers, classical bit order, `classical_counts`,
`last_classical`, and bounded `shot_results`. A shot record contains its one-based
number, counts outcome, final memory and ordered measurement events with aligned
qubits, bits and destinations. Metadata advertises counts kind, execution version,
seed, returned-record count and truncation. Marginal per-operation histograms remain
available separately from joint final-memory counts and individual histories.

Only the last shot's quantum statevector is returned. Exact probabilities derive
from its amplitudes; they are not aggregate probabilities of all trajectories.
Empirical aggregate frequencies remain `counts / shots`.

## Frontend and persistence

The existing builder gains opt-in classical configuration, register name/size
controls, destination selectors, bit/register equality selectors, an optional seed,
and optional history count. Register renames preserve references; invalid/duplicate
names retain the previous name. Invalid mappings and comparison values are rejected
before submission. Dragging preserves classical references independently of quantum
qubit movement. Quantum controls use dots, classical controls show IF labels,
measurement uses M and reset uses |0⟩.

Results separate aggregate counts, statevector/probabilities, last-shot classical
memory, explicit measurement marginals, and expandable per-shot histories. Histories
are never requested by default and the UI renders only the bounded requested subset.

The existing Circuit → CircuitVersion → SimulationRun → SimulationResult transaction
is preserved. Register definitions/conditions are stored in circuit JSON; bounded
histories and metadata use existing result JSON. The existing `num_classical_bits`
column is populated for classical-mode circuits. No migration or history rewrite
was necessary. Authenticated retrieval and older JSON-only result shapes were tested.

## Verification results

| Check | Result |
| --- | --- |
| Entire backend suite against isolated PostgreSQL | **358 passed, zero skipped** |
| New Phase 2 backend coverage | **132 cases**, all included in that suite |
| Frontend suite | **All five test files passed** |
| Backend Ruff | Passed |
| Frontend ESLint | Passed |
| Frontend TypeScript | Passed |
| Frontend production build | Passed |
| Unchanged Phase 1 browser suite | Passed, including all 21 palette operations |
| Phase 2 production browser + real API | Passed |
| Whitespace/diff check | Passed |
| Visual inspection | Result screenshot inspected; distinct count/state/memory/history panels |

The Phase 2 browser checks exercised Bell correlations, classical feed-forward,
per-shot opposite sequential measurements, reset preserving classical memory,
seeded repeatability, named registers, whole-register equality, renaming existing
references, validation before submission, and mobile horizontal width. Counts were
checked against all 128 returned shot outcomes. Simulation responses were not mocked.
The screenshot stayed in `/tmp` and was not committed.

Backend tests include all required conditional gates (X/Y/Z/H/RX/RY/RZ/S/T,
CNOT/CZ/SWAP and CRX) under true and false comparisons, classical versus quantum
controls, grouped/reversed mappings, overwritten and skipped writes, fresh state
per shot, normalization after individual operations, register/bit validation,
resource bounds, seed isolation, guest execution, authenticated persistence and
historical retrieval. Existing tests and the Phase 1 browser script were unchanged.

The remaining backend warning is an upstream Starlette/AnyIO deprecation. Next.js
reports the existing `next lint` command's future deprecation.

## Exact verification commands

From the repository root (the Phase 1 isolated database and Playwright installation
were reused):

```bash
TEST_DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check backend/.venv/bin/python -m pytest backend/tests -q
backend/.venv/bin/ruff check backend/app/
git diff --check
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2.cjs
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase2.cjs
SIMULATOR_SCREENSHOT=/tmp/simulator-v2-phase2.png NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase2.cjs
cd frontend
npm test
npm run lint
npm run typecheck
npm run build
```

Local server commands used, in separate terminals:

```bash
# Repository root:
DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
# frontend/:
PORT=13002 npm run start
```

Fresh database/tool setup is documented in [simulator verification commands](SIMULATOR_V2.md#verification-commands).

## Limits and recommended Phase 3

The limit remains 10 qubits and 500 operations. Shots are at most 100,000, subject
to the documented 20-million-unit full-circuit workload budget. At most 256 shot
records and 20,000 measurement values are returned; default is no shot records.
The full-shot workload guard can reject exceptionally large legacy requests that
previously reused one unitary state. Requests fail clearly rather than reducing shots.

Only equality conditions and measurement writes are supported: no classical
arithmetic, loops, arbitrary expressions, density matrices, noise or hardware.
Per-operation histograms are marginal; only returned histories retain overwritten
observations. The last quantum trajectory must not be mistaken for a mixed-state
ensemble. Seed streams are reproducible for this execution version, not guaranteed
across future engine changes. Builder seeds are limited to exact JavaScript integers;
the API accepts non-negative 63-bit integers.

Recommended Phase 3: a **bounded shot debugger with selected quantum/classical
checkpoints and reusable conditional blocks**. The executor already separates
quantum state, classical state, condition evaluation and event history; it can expose
those boundaries without creating new gate implementations. Currently only final
quantum state is inspectable, which limits diagnosing intermediate branches. Define
trace size and persistence semantics before adding checkpoints. Keep noise
or density-matrix simulation separate until an explicit ensemble result contract
exists; the current trajectory statevector must not be repurposed ambiguously.
