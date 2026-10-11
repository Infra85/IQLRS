# Learning ↔ builder integration

## Repository architecture recovered before implementation

The Phase 1 bundle is `backend/data/modules.json`, validated by
`schemas/curriculum.py` and synchronized into `frontend/src/app/learn/modules.ts`.
Its integer module IDs map to stable database UUIDs through `services/curriculum.py`.
Each module already has stable experiment/challenge descriptors. They contain
pedagogical metadata, but no executable validation rules.

`CircuitBuilder.tsx` owns gates, qubit count, classical registers and results in
React state. Gate placement uses `edit-circuit.ts`; measurement destinations and
conditions use `classical-circuit.ts`. Initial freeform state is two empty wires.
Clear removes operations and results. There is no general saved-circuit loader or
local draft persistence in the current builder. Authenticated simulation saves a
Circuit, CircuitVersion, SimulationRun and SimulationResult; `/runs/{id}` reads
these under ownership checks. Errors appear inline. Module-only query parameters
previously did not initialize a lesson circuit. Bell/Grover query parameters used
local definitions and run-time sequence/probability checks.

The existing `CircuitRequest` is the only circuit serialization format. Simulation
uses `qiskit_runner.run_circuit`, a compatibility entrypoint into Simulator V2.
Qubit zero is the least significant bit; displayed quantum strings are q(n−1)…q0.
Classical strings use `classical_bit_order`, with high bits first within registers.
A dynamic circuit's statevector represents its last conditional trajectory, not
an ensemble. Counts and classical counts are finite-shot samples. This distinction
must remain explicit in educational validation.

The sections below describe the implemented Phase 2 slice.

## Domain contract and curriculum integration

`backend/data/challenges.json` supplies the execution companion to **all 16 existing
Phase 1 activity IDs**. It does not create a second set of curriculum identities.
`learning_challenges.load_definitions()` joins each entry to the validated Phase 1
bundle and verifies module, type, title, difficulty and objective. Unknown IDs,
duplicate IDs, missing activities, malformed starters/targets and unknown validators
fail initialization and CI. The original lesson/quiz JSON remains byte-for-byte
unchanged. Its `status: planned` describes the Phase 1 descriptor; availability is
now supplied by the executable activity API. Do not use that historical descriptor
flag as the runtime feature gate.

A definition contains an explicit version, existing activity/module IDs, instructions,
reflection, starter `CircuitRequest`, progressive hints, prediction labels and
trusted composed rules. `ChallengeDefinition` and `Rule` validate this contract.
The public API omits rules, expected answers and unrevealed hints. Rule targets are
returned with a completed validation as structured `expectation` data, and stored
with the attempt so later content changes do not erase the assessment context.
No frontend component defines a challenge or decides correctness.

The existing Phase 1 seed/upgrade mechanism is untouched. Executable definitions
are version-controlled resources loaded by the service, so they need no repeated
DB seeding, mutable public definition API or Challenge table. Publish upgrades by
incrementing the affected activity's version; old attempts remain immutable, old
completion stays visible, and stale request versions return 409. A stale workspace
is not restored into a newer activity. Historical circuits can be explicitly
restored, then committed as a new revision under the current definition.

## Learner lifecycle

1. The lesson renders its existing experiment and challenge descriptors, with
   explanatory activity links and separate completion indicators.
2. `/builder?module=4&challenge=m4-challenge` resolves authenticated server context.
   Module-only URLs resolve the module's first activity; `module-4` is also accepted.
   Historical `challenge=bell` and `challenge=grover` aliases resolve server-side.
3. The builder loads the saved workspace or the editable starter. A bad context
   leaves an actionable error rather than silently becoming a freeform challenge.
4. Learners enter normalized probabilities (or conceptual arithmetic) and **Commit
   prediction**. The server stores the circuit, prediction, revision UUID and hash.
5. **Run experiment / Run simulation** executes the committed circuit. Editing
   circuit, registers, qubits, shots or prediction invalidates the UI commitment.
   Repeat Run for one revision reuses its trusted result; Try again + Commit makes
   a fresh run. Run never creates a graded attempt or completes an activity.
6. The comparison shows prediction, ideal probabilities when available, sampled
   outcomes and an authored reflection. Incorrect predictions do not reduce scores.
7. **Validate challenge** consumes the trusted saved run, evaluates all rules, and
   records an immutable attempt. Conceptual activities use **Validate reasoning**
   without a simulator or circuit canvas.
8. Manual hints reveal progressively and persist independently of success. Retry,
   Reset to starter/Reset answers and restoring historical work retain all history.
9. **Save circuit to my history** copies the trusted run into the existing Circuit,
   CircuitVersion, SimulationRun and SimulationResult models without rerunning.
   The saved ID makes repeats idempotent. Ordinary freeform saving is unchanged.

Committed work survives reload. Edits made after the last commitment are working
state until committed again; there is no claim that every uncommitted keystroke is
persisted. The UI explicitly identifies changed work that needs a new commitment.
Activity controls enforce the same three-qubit/2048-shot limits as the API; a
commit sends the displayed shot count without silently changing it. Conceptual
answers must be bounded integers. Switching activity context or returning to the
freeform builder initializes that context independently, including after a
conceptual activity. Comparison tables include unexpected observed outcomes even
when a learner changes the circuit's output width.

## Semantic validators

| Type | Behavior |
|---|---|
| `constraints` | Required normalized operations/targets, allowed gate set, maximum gate count and an explicit preserved starter prefix. Syntax checks are limited to pedagogically declared scaffolds. |
| `state_equivalence` | Pure-state fidelity `abs(<target\|actual>)² >= 1−1e−8`. Global phase is irrelevant; relative phase matters. Rejects dynamic/last-shot statevectors as pure ensemble evidence. |
| `probability` | Full distribution comparison, including expected zeros, with absolute tolerance 0.02. Uses ideal unitary/pre-terminal-measurement probabilities, not noisy shot counts. |
| `correlation` | Joint distribution check for balanced correlated Bell outcomes, not separate qubit marginals. Combined with state fidelity for Φ+; does not claim a Bell-inequality test. |
| `classical_output` | Ideal measured distribution plus actual register mapping `c1c0`. Deutsch–Jozsa only classifies its input register, with q2 auxiliary. |
| `teleportation` | Preserves the protocol scaffold, permits conditional X/Z corrections on Bob q2, checks all four Alice branches and three input preparations using Simulator V2, then compares Bob's reduced-state overlap. |
| `conceptual` | Deterministic finite integer arithmetic answers for the N=15 order/factor example and a=14 counterexample. No quantum execution is implied. |

The simulator is unchanged. Unitary Run needs one simulator call. Terminal
measurements additionally use a **one-shot preparation probe** to obtain ideal
probabilities before collapse and map them through the simulator's actual classical
bit order. This is necessary to avoid treating a last-shot vector as an ensemble.
Unsupported dynamic probability patterns fail the objective instead of guessing.
Renaming or removing classical memory required by an authored scaffold produces
failed objective checks, rather than a validator service error.

Teleportation validation performs 12 deliberately distinct probes: 4 forced
measurement branches × 3 input states (`RY(.73); RZ(.41)`, \|0⟩ and |+i⟩).
The engine's existing RNG injection seam forces the two equiprobable outcomes;
no gates, state updates or measurement semantics are implemented in the adapter.
The starter and allowed tail ensure exactly two Alice measurements. This is a
**guided protocol grader**, not an unrestricted teleportation theorem prover.

Prediction comparisons use absolute tolerance 0.03 against ideal probabilities.
For dynamic sampled-only output the tolerance is `max(0.03, 2/sqrt(shots))`, a
conservative four-standard-error envelope at p=1/2. Predictions are formative:
sampling variation never changes completion or score. Teleportation completion
uses exhaustive branch probes, not observed branch counts.

## Result contract and scoring

Every validator contributes `{id, passed, message}` checks. Validation returns:

```json
{
  "result": {
    "status": "success",
    "passed": true,
    "score": 90,
    "checks": [{"id": "qubit_count", "passed": true, "message": "…"}],
    "feedback": {"summary": "…", "details": [], "explanation": "…"},
    "expectation": {"prediction": {"00": 0.5, "11": 0.5}, "rules": []},
    "hintsUsed": 1,
    "challengeId": "m4-challenge",
    "moduleId": 4,
    "version": 1
  },
  "attempt": {"id": "uuid", "number": 2, "hintsUsed": 1, "score": 90, "passed": true, "status": "success", "version": 1, "createdAt": "…"},
  "completed": true,
  "comparison": {"matches": true, "prediction": {}, "actual": {}, "ideal": {}, "basis": "ideal probabilities", "tolerance": 0.03}
}
```

Status is `success`, `near_miss` (some substantive checks pass), or `incorrect`.
The frontend contract also supports `invalid_circuit`; malformed submissions are
currently rejected at the request boundary with friendly 422 errors instead of
creating bogus attempts. Missing context: 404; module mismatch: 422; stale version,
revision or missing Run: 409; oversized body: 413; rate limit: 429; transient
simulation/persistence/validator failure: 503. No stack traces reach learners.

Completion score is `max(50, 100 − 10 × hints revealed)`; incomplete attempts score
0. Hint count is cumulative for the activity workspace so creating a retry cannot
forge a zero-hint score. Best historical score is retained. Runs, predictions,
failed attempts and elapsed time have **no penalty**. Activity completion and quiz /
module completion are independent; no existing progress row is changed.

## Persistence and resource limits

Alembic `0003_learning_challenges` adds two tables:

- `challenge_workspaces`: one row per user/activity; current version/revision,
  fingerprint, bounded circuit/prediction/run and cumulative hint count.
- `challenge_attempts`: immutable numbered submissions, version, revision,
  circuit, prediction, compact simulation summary, complete validation/expectation,
  hints, score, created/completed timestamps. Completion and best score derive
  from successful attempts; no duplicate completion table is necessary.

User-row locks serialize writes across workers. Unique constraints enforce one
workspace and one attempt per user/activity/revision and per attempt number.
A repeated revision returns the original attempt. Reusing its key with changed
content is rejected. The service never accepts client scores, passes, targets,
solutions or hint counts. Ownership always comes from authenticated `User`.
An old attempt revision cannot be resubmitted under a newer definition version;
its unchanged assessment remains available through the historical-attempt API.

Limits: 32 KiB request body (including chunked requests), 24 KiB serialized
circuit, 1–3 qubits, 64 sequential operations, at most 3 classical bits, 1–2048
shots, at most 16 prediction values with finite numbers and bounded labels.
Simulator V2's own structural/work checks also apply. No debug traces or shot
history are accepted by activity APIs. Attempts store counts/ideal probabilities
and metadata, not repeated statevector/trajectory dumps. A workspace holds only
its latest bounded result. At 200 historical attempts per user/activity, further
Validate requests return 409 while Run remains available; history is never deleted.
Existing shared PostgreSQL rate limiting allows 30 Run/Validate calls per minute
and 60 commitment/hint/save writes per minute per client address.

The migration adds tables only; downgrade removes these two feature tables only.
`app.migrate` excludes Alembic-owned tables from legacy `create_all` bootstrapping.
The legacy integer-ID bridge now does the same: otherwise it would pre-create new
Alembic tables and collide with their migrations. This compatibility correction
is covered through the complete migration entrypoint, including repeated startup.
No existing user, quiz, progress, circuit, simulation or AI record is rewritten.

Structured event names include `challenge_configuration_failure`,
`challenge_invalid_circuit`, `challenge_simulation_rejected`,
`challenge_simulation_failure`, `challenge_validation_failure`,
`challenge_objective_not_met`, `challenge_persistence_failure` and
`challenge_circuit_save_failure`. Logs contain activity/version/check IDs and
server-side diagnostic exceptions, never tokens, passwords or full learner payloads.

## API inventory

All routes require the existing bearer authentication:

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/challenges` | Activity inventory with own completion and best score |
| GET | `/api/challenges/{id}?module=4` | Trusted public definition, own workspace, hints and attempt summaries |
| PUT | `/api/challenges/{id}/prediction` | Commit circuit + prediction under version/revision |
| POST | `/api/challenges/{id}/run` | Execute or return trusted cached run + comparison |
| POST | `/api/challenges/{id}/validate` | Semantic evaluation and idempotent submission |
| POST | `/api/challenges/{id}/hints` | Reveal the next hint, idempotently by index |
| POST | `/api/challenges/{id}/save-circuit` | Save cached run to existing simulation history |
| GET | `/api/challenges/{id}/attempts/{number}` | Own historical circuit, prediction and structured result |

## Module inventory

Every listed activity has prediction commitment, validation, retry, persisted
attempts and independent completion. Circuit activities predict distributions;
Module 8 commits arithmetic answers. The JSON file is the machine-readable inventory.

| Module | Stable ID | Experience | Validation |
|---|---|---|---|
| 1 | `m1-experiment` | Create a superposition | Probability + \|+⟩ state fidelity |
| 1 | `m1-challenge` | Prepare \|1⟩ with X | Gate/target/count constraints + state fidelity |
| 2 | `m2-experiment` | Compare two superpositions | Four-outcome probability + product-state fidelity |
| 2 | `m2-challenge` | Undo a product superposition | Preserved H/H starter + \|00⟩ fidelity |
| 3 | `m3-experiment` | Compare Z and X readouts: direct \|+⟩ measurement | Preparation/measurement constraints + ideal Z distribution |
| 3 | `m3-challenge` | Predict before measuring: \|0⟩ X readout | H/readout constraints + ideal distribution; rotated conditional states explained |
| 4 | `m4-experiment` | Create and decode a Bell pair | Preserved Bell starter + decoded \|00⟩ fidelity |
| 4 | `m4-challenge` | Prepare \|Φ+⟩ | State fidelity + probability + joint correlation |
| 5 | `m5-experiment` | Compare simple promised oracles: constant zero | Fixed identity-oracle starter + c1c0=00 |
| 5 | `m5-challenge` | Classify a promised instance: f(x1x0)=x0 | Fixed balanced-oracle starter + c1c0=01 |
| 6 | `m6-experiment` | Amplify \|11⟩ | Preserved preparation/CZ oracle + marked-state fidelity |
| 6 | `m6-challenge` | Complete the diffusion step | Same scaffold and semantic amplified-state goal |
| 7 | `m7-experiment` | Trace all four correction branches | Guided branch-complete receiver validation |
| 7 | `m7-challenge` | Choose receiver corrections | Guided branch-complete receiver validation |
| 8 | `m8-experiment` | Compare useful and unhelpful orders | a=2 and a=14 modular arithmetic/gcds |
| 8 | `m8-challenge` | Trace factoring from an order | Same verified arithmetic with quantum/classical distinction |

Modules 6–8 intentionally reuse guided experimental scaffolds between experiment
and challenge; these are separate stable Phase 1 activities, not an adaptive engine.

## Flagship example: `m4-challenge`

- Initial state: \|00⟩; starter: two empty wires.
- Goal: (\|00⟩ + \|11⟩)/√2, in q1q0 order.
- Expected Z probabilities: 00=0.5, 01=0, 10=0, 11=0.5.
- Validation: fidelity at least 1−1e−8, probability tolerance 0.02 and joint correlation.
- H(q0) followed by CNOT(q0,q1) works. H(q1) followed by CNOT(q1,q0)
  also works. A global phase passes; Φ− fails fidelity while passing Z distribution,
  yielding a near miss that explains relative phase.
- Hints: create superposition; try H(q0); use q0 as CNOT control and q1 as target.

## Adding an activity or validator

1. Add the stable descriptor/objective/module relationship in the authoritative
   curriculum bundle using Phase 1 content-upgrade guidelines. Synchronize frontend
   curriculum with `node frontend/scripts/sync-curriculum.cjs`.
2. Add its execution companion to `backend/data/challenges.json`, reusing the exact
   activity ID and metadata. Use only the existing `CircuitRequest` format.
3. Compose existing rules, explicit tolerances, starter, meaningful instructions,
   reflection, labels and progressive hints. Increment versions when meaning changes.
4. Add a reproducible passing circuit/answer to
   `backend/tests/fixtures/learning_challenges.json`, plus negative/scientific tests.
5. Regenerate the cross-language fixture:
   `PYTHONPATH=backend backend/.venv/bin/python backend/scripts/export_challenge_contract.py`.
6. Run backend, frontend, typecheck, build and browser checks. No module-specific
   edits to the lesson renderer, activity panel or builder should be necessary.

For a new validator, extend the typed Rule discriminator and registry, configuration
validation and semantic dispatch in `services/learning_challenges.py`. Keep execution
in Simulator V2. Add correct/incorrect/malformed and tolerance tests and ensure the
common result contract remains valid. Do not introduce a circuit JSON equality
validator as the general correctness mechanism.

## Testing and manual review

`backend/tests/test_learning_challenges.py` covers all 16 reference experiences,
malformed schemas/circuits/states, phase equivalence, tolerance boundaries, finite
shots, misleading Bell marginals, classical bit order, teleportation branch errors,
forged inputs, stale versions/revisions, ownership, rate limits, duplicate/concurrent
submissions, failure recovery, migration upgrade/downgrade and legacy upgrades.
`test_curriculum_science.py` continues independently checking Phase 1 mathematics.

`frontend/tests/fixtures/challenge-contract.json` is generated by real backend
validators. Backend tests fail if it drifts; frontend tests parse it through the
runtime decoder and render result/comparison components. Other frontend tests check
prediction normalization, commitment invalidation and absence of module-specific
definitions. Existing editor, narration, quiz and simulator tests remain in place.

`frontend/tests/browser/learning-challenges.cjs` logs in via the real UI, checks
links in all eight lessons, exercises the Bell failure/hint/correction/reload path,
completes all 16 activities, checks mobile conceptual layout, shot/qubit limits and
client navigation from conceptual to freeform mode, and confirms legacy links and
quiz compatibility. It respects API `Retry-After` when full-curriculum coverage
exceeds the normal request budget. Supply
`PHASE2_EMAIL`, `PHASE2_PASSWORD`, optionally `PHASE2_URL` and `CHROME_PATH`; use a
verified account in an isolated migrated test database, never production credentials.
`NODE_PATH` may point at a temporary Playwright install. The browser test can be
repeated without deleting learner history.

Manual visual review includes desktop teleportation and mobile conceptual Shor.
The reviewed UI separates the guided-learning header, conceptual answer labels,
correction controls, prediction comparison, hints and historical attempts. No new
color-only status indicators are used. Native inputs, buttons, details/summary,
labels and status/alert regions provide keyboard access and readable feedback.
Final measured test counts, recovery classifications, changed files and remaining
limitations are in [the Phase 2 recovery report](PHASE2_RECOVERY_REPORT.md).
