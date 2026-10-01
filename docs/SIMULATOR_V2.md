# Simulator V2 — Phase 2

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
- Nonunitary: MEASURE on one or several qubits, MEASURE_ALL, RESET on one qubit.

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
Unitary targets contain one qubit except SWAP (two). MEASURE accepts a nonempty
list of distinct targets; MEASURE_ALL implies ascending q0…q(n−1). SWAP also accepts the
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

## Classical registers and conditions

`classical_registers` is an ordered list of `{ "name": "c", "size": 2 }` objects.
Names are case-sensitive, unique, start with an ASCII letter, and contain only
letters, digits and underscores (maximum 32 characters). Every shot initializes
all bits to integer zero. Classical bit 0 is the least-significant bit within its
register; whole-register equality uses that binary integer interpretation.

Measurements map each target position to the corresponding `destinations` entry.
Destinations reference `{ "register": "c", "bit": 0 }`. Multiple writes to the
same bit in different operations are allowed: the latest write wins in memory,
while shot history retains earlier observations. Duplicate destinations within
one measurement are rejected. RESET never writes or clears classical memory.

```json
{
  "num_qubits": 2,
  "shots": 128,
  "seed": 42,
  "shot_record_limit": 128,
  "classical_registers": [{"name": "c", "size": 2}],
  "gates": [
    {"type": "H", "qubit": 0},
    {"type": "MEASURE", "qubit": 0,
     "destinations": [{"register": "c", "bit": 0}]},
    {"type": "X", "qubit": 1,
     "condition": {"register": "c", "bit": 0, "operator": "eq", "value": 1}},
    {"type": "MEASURE", "qubit": 1,
     "destinations": [{"register": "c", "bit": 1}]}
  ]
}
```

This produces only `00` and `11`. `condition` wraps **any** existing operation,
including controlled/parameterized gates, SWAP, measurement and reset. It is
evaluated immediately before that operation, against current classical memory.
`operator` must be `eq`; values must be integers 0/1 for a bit or between 0 and
`2^size−1` for a whole register. Omit `bit` (or set it to null) for register equality,
e.g. `{"register":"c","operator":"eq","value":3}`. Conditions on unwritten bits
read their initialized zero. There is no arbitrary expression parser.

Classical conditions are separate from quantum `controls`: a condition first
chooses whether to execute the operation; quantum controls then govern which
amplitude pairs its matrix affects. No conditional gate implementations are
needed; all Phase 1 matrices and primitives are reused.

## Sequential measurement, reset, and shots

Each shot allocates a fresh |0…0⟩ statevector, fresh zero-valued classical memory,
and a fresh measurement history. It executes **every operation in sequence**;
there is no shared simulated prefix or counts synthesized from a single execution.
Matrices are compiled once per request, which does not share state across shots.

MEASURE samples Born probabilities, collapses and renormalizes the quantum state,
writes the specified classical destination, then proceeds to the next operation.
Multi-target measurements process targets in supplied order, preserving quantum
correlations. Reported event qubits/bits/destinations are aligned in descending
qubit order. Operations after measurement act on the sampled collapsed state.
For `H q0; measure q0→c0; X q0; measure q0→c1`, every shot has `c1 = NOT(c0)`.

RESET internally measures its target and applies X for outcome 1. Entangled
partners retain the sampled **conditional** state; the target ends in |0⟩.
Internal reset samples do not appear as explicit classical measurement records,
and prior classical observations remain available to subsequent conditions.

Randomness is request-local: `random.Random(seed)`. A supplied seed reproduces
counts, histories, and the final state for identical requests on this execution
version. No global Python RNG is seeded or consumed. Omitted/null seed uses fresh
system-provided initialization. Changing the requested history limit does not
change sampled outcomes. Cross-version seed-stream compatibility is not promised.

## Counts, histories, and compatibility

`metadata.counts_kind` explicitly distinguishes the two result modes:

- **Classical:** circuits using registers, destinations or conditions, with at least
  one explicit measurement. `counts` aggregates final measured classical memory.
  `classical_bit_order` defines labels: registers in declaration order, then bits
  descending within each register. Only destinations mapped by measurement
  operations appear. A mapped bit whose conditional writes were all skipped is
  `x`, not a fabricated measurement of zero. If an earlier write occurred, that
  value remains even when a later conditional write is skipped.
- **Quantum:** circuits without explicit measurements retain final computational
  basis sampling. Completely legacy payloads also retain Phase 1 quantum-readout
  `counts`, even when they contain measurement/reset. The terminal readout uses
  the same measurement primitive on a copy, preserving the exposed final state.

Legacy payloads require no registers or destinations. Internally they receive
implicit `c` memory of size `num_qubits`, with q[i] measurements writing c[i].
Their legacy last-shot `measurements` shape remains unchanged. Supplying any new
classical feature opts into explicit mappings: every measurement must specify its
destinations. If registers are omitted in that mode, the implicit `c` register is
still available. An explicitly empty register list is invalid.

Result fields:

- `counts`: joint final outcomes in the mode above, aggregated over **all** shots.
- `classical_registers`: effective ordered register definitions.
- `classical_bit_order`: exact destination order of classical histogram labels.
- `classical_counts`: joint final measured-memory histogram, also available in
  legacy mode; empty when there are no explicit measurements.
- `last_classical`: full initialized memory from the last shot, with each register
  displayed highest bit first. Unmapped bits remain zero; this is memory, not a
  claim that those bits were measured.
- `shot_results`: first `min(shots, shot_record_limit)` shot records, ordered by
  one-based `shot`; each has `outcome` (the counts key), `classical` memory snapshot,
  and ordered `measurements`. Each event includes zero-based `operation`, descending
  `qubits`, `bits`, and aligned `destinations`. These histories preserve joint
  relationships and overwritten observations. No per-shot statevectors are stored.
- `statevector`: last shot's final `[real, imaginary]` amplitudes. With no
  measurement/reset it is the exact unitary state; otherwise it is one conditional
  pure trajectory, **not** an ensemble average. Its exact probabilities are derived
  as real² + imaginary² and must not be confused with aggregate count frequencies.
- `measurements`: last-shot explicit events (destination information is additive
  in classical mode). The final state may differ after subsequent operations.
- `measurement_counts`: per-operation **marginal** histograms. Conditional
  measurement histograms count only shots in which that operation executed.
- `metadata`: engine, `execution_version: 2`, shots, seed, `counts_kind`, quantum
  bit order, `statevector_scope`, `shot_records_returned`, `shot_records_truncated`.
- `simulation_id`, `circuit_diagram`: existing fields.

Signed-in circuit definitions and bounded shot records use existing JSON columns.
The existing circuit `num_classical_bits` field records allocated size for new
classical-mode requests. `SimulationResult.probabilities` remains empirical
`counts / shots` in the advertised counts mode. Run retrieval returns new fields
beside historical `amplitudes`; old rows lacking these fields remain readable.
There is no schema migration, data rewrite, or change to ownership checks.

## Builder and validation

Choose a gate and wire, or drag a gate. Linked operations select two wires. The
angle editor accepts finite decimal/scientific radians and simple expressions such
as `pi`, `-pi/2`, `3*pi/4`, and `π/2`, without evaluating code. Existing rotation
angles can be edited below the palette; edits commit on blur, and invalid edits
report an error and retain the previous angle. API payloads always contain numbers,
not expressions. The API rejects missing/nonfinite parameters, invalid indices,
duplicate indices, unsupported operations, and malformed payloads via 400/422
responses. The builder checks circuit indices and parameters before submitting.

Enable **Classical registers** to opt into explicit memory. Configure names/sizes,
add registers, and choose each measurement's destination in its operation row.
Register renames commit on blur and preserve references; invalid/duplicate names
are rejected without changing references. Each operation has a **Classical
condition** selector (bit or register), equality value, and an **Always execute**
option. Quantum controls retain dots; classical conditions use textual IF badges
and labels; measurement uses M and reset uses |0⟩. Existing drag/keyboard placement
preserves destinations and conditions when moving an operation.

Seed input is optional (the browser accepts non-negative safe integers). Enable
shot history before execution to request 1–256 records; default selection is 20.
Results separate aggregate counts, last-shot classical registers, expandable shot
history, and quantum amplitudes/probabilities. Only the bounded requested subset
is rendered, and no shot records are returned by default.

## Limits

- 1–10 qubits, at most 500 operations; API shots 1–100,000, builder shots 1–8,192.
- 1–8 named registers with at most 32 classical bits total.
- Optional seed: integer 0 through 2^63−1. Browser inputs are limited to safe JS
  integers (at most 2^53−1).
- Returned shot records: 0–256, default zero. Requested records multiplied by
  measurement target count across the circuit must not exceed 20,000 values.
- Every circuit is subject to `shots × work_per_shot × 2^qubits ≤ 20,000,000`.
  `work_per_shot` is the sum of one per ordinary/reset operation or target count
  per measurement, plus 1 for classical readout or `num_qubits + 1` for quantum
  readout. This includes the full sequence, even when conditions skip operations.
  Very large legacy requests can now exceed this budget because shots execute
  independently. Rejected requests receive a clear error; reduce shots or circuit
  complexity. There is no silent shot reduction.
- Conditions support equality only. No classical arithmetic, boolean expressions,
  loops, arbitrary initial states, noise models, density matrices, symbolic
  parameter binding, alternative runtimes or hardware execution.
- Only one final quantum trajectory is returned, never all per-shot statevectors.
- The builder offers single quantum controls and per-qubit/measure-all mapping.
  Multiple quantum controls, inverse phase gates, and arbitrary grouped measurement
  targets remain available through the API.

See [Phase 2 engineering report](SIMULATOR_V2_PHASE2_REPORT.md) for verification
results and the next scope justified by this implementation. The [Phase 1
report](SIMULATOR_V2_PHASE1_REPORT.md) is preserved as a historical record.

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
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase2.cjs
```

Browser overrides: `CHROME_PATH` selects the Chrome executable, `BUILDER_URL`
selects the frontend origin. The script uses a new guest context and checks all
21 palette operations, angle editing/validation, serialization, actual API
responses, Bell collapse/reset, result labels, and mobile horizontal overflow.

The Phase 2 browser suite additionally exercises the four representative circuits
(Bell, classical feed-forward, sequential opposite measurements, reset retaining
memory), named registers, whole-register comparisons, seed repeatability,
pre-submit validation, histories, and mobile layout. Optional
`SIMULATOR_SCREENSHOT=/tmp/simulator-v2-phase2.png` captures the result view for
visual inspection. Both suites use the real backend without mocked results.
