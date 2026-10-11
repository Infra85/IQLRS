# Curriculum Phase 2 recovery audit

Recovery date: 2026-10-09. Starting HEAD: `ae3ff38`
(`feat(curriculum): complete scientific content and validation pass`).
Recent parent merges already included Simulator V2 Phases 1–4. Curriculum Phase 2
was uncommitted: 8 modified tracked files and 17 untracked files. Recovery began
with `git status --short`, the complete tracked diff, untracked implementation,
data and tests, and recent commit history. No reset, revert, clean, or checkout
replacement was performed. Completed components were retained.

## State found and recovery outcome

“DONE” at intake means an implementation existed and survived the audit; runtime
results below are the verification evidence. The initial suspicion of a missing
bit in partial-measurement mapping was ruled out by inspecting Simulator V2's
measured-bit ordering. The reproduced validator defect concerned changed scaffold
registers instead.

| Area | Intake | Final | Evidence / recovery work |
|---|---|---|---|
| Challenge models | DONE | DONE | Existing workspace and immutable attempt models retained |
| Curriculum challenge definitions | DONE | DONE | All 16 stable Phase 1 IDs retained; no curriculum JSON changes |
| Validation layer | BROKEN | DONE | Renamed/missing scaffold registers now fail objective checks instead of raising service errors |
| Challenge API | DONE | DONE | Existing authenticated routes retained; old revision replay under a new version now rejected |
| Prediction flow | PARTIAL | DONE | Removed silent shot truncation; UI and API agree on limits and integer answers |
| Feedback | DONE | DONE | Existing structured feedback retained; unexpected output labels now visible in comparison |
| Hints | DONE | DONE | Existing progressive disclosure and cumulative usage retained |
| Attempt persistence | DONE | DONE | Existing idempotency, ownership, concurrency and history retained and tested |
| Completion persistence | DONE | DONE | Existing successful-attempt derivation retained; independent of quizzes |
| Builder challenge mode | PARTIAL | DONE | Context changes reinitialize the builder; activity limits enforced without reducing freeform limits |
| Frontend challenge UI | PARTIAL | DONE | Existing panel and lesson integration retained; navigation and returning-learner paths verified |
| Tests | PARTIAL | DONE | Added recovery regressions and all-activity browser coverage; updated stale curriculum selectors/links |
| Migrations | PARTIAL | DONE | Existing additive migration retained; populated-record preservation and repeated entrypoint checked |
| Documentation | PARTIAL | DONE | Existing system guide updated and this measured recovery report added |

## What already existed

The interrupted implementation already supplied definitions for eight experiments
and eight challenges; seven validator types delegating quantum execution to
Simulator V2; authenticated prediction, run, validation, hint, history and circuit
save APIs; additive persistence; independent activity completion; builder and
lesson components; cross-language fixtures; extensive backend tests; and a system
guide. The baseline full backend suite passed 616 tests with two opt-in hardware
tests skipped. The baseline frontend passed 43 tests, typecheck, lint and build.

## What recovery changed

- Corrected objective validation when a valid learner circuit renames the
  classical register required by the authored scaffold. Three real API regression
  cases cover measurement, Deutsch–Jozsa and teleportation.
- Rejected replaying an old attempt UUID under a newer definition version while
  preserving its original result and historical completion.
- Made activity controls enforce three qubits and 2048 shots and submit exactly
  the displayed shot count. Freeform retains ten qubits and 8192 shots.
- Aligned conceptual input validation with the API's bounded integer contract.
- Scoped builder component state to URL activity context, fixing client navigation
  from a conceptual activity back to the freeform builder.
- Included unexpected circuit outcomes in comparison tables instead of hiding
  outcomes absent from the prediction labels.
- Strengthened migration tests with populated quiz attempts, historical answers,
  progress, saved circuits, versions, runs and results. Compared every existing
  model table's complete contents before and after migration cycles.
- Expanded E2E coverage to all 16 activities, limits and navigation. Repaired
  curriculum E2E assumptions about old builder links and a single article/badge;
  added waits for client navigation and honored real API rate limits.

## Verification

All database checks used a new isolated PostgreSQL 18.6 cluster under
`/tmp/iqlrs-recovery-pg`, port 55439, database `iqlrs_recovery`. Browser checks used
a dedicated verified test learner, the real local API, and the production Next.js
build at `http://127.0.0.1:13002`. No existing application database was migrated.

| Check | Result |
|---|---|
| Full backend: `python -m pytest backend/tests -q -rs`, with `TEST_DATABASE_URL` | **620 passed, 2 skipped**, 34.77 seconds |
| Included challenge backend tests | **67 passed** as part of the full suite |
| Backend Ruff: `ruff check backend/app` | Passed |
| Frontend: `npm test` | **45 passed**, zero failures/skips |
| Frontend: `npm run typecheck` | Passed |
| Frontend: `npm run lint` | Passed; Next.js reports the existing CLI deprecation |
| Frontend: `npm run build` | Passed; standalone production output generated |
| Challenge browser: `frontend/tests/browser/learning-challenges.cjs` | **19 passed**, zero failures/skips, 79.69 seconds; all 16 activities plus integration regressions |
| Curriculum browser | Passed: 8 lesson renders, 24 answers/explanations, 8 real quiz submissions/retries, 16 activity links |
| Simulator V2 browser | Passed: all 21 operations, serialization, rotations, measurement/reset, mobile layout |
| Simulator V2 classical browser | Passed: registers, feed-forward, sequential collapse, reset memory, seeded shots, bounded history, mobile layout |
| Simulator V2 debug browser | Passed: tracing, shot/checkpoint selection, conditions, reset, amplitudes, highlights, mobile layout |
| Hardware-disabled browser | Passed: no hardware controls; local simulation remains usable |
| Hardware-enabled browser, fake provider | Passed: discovery, validation, confirmation, queued/running/completed states, results/comparison, refresh, failure, ownership, idempotency and mobile layout |
| `git diff --check` | Passed |

The two backend skips are the explicitly opt-in live IBM/Braket QPU tests.
Desktop teleportation and 390-pixel-wide conceptual activity screenshots were
visually inspected; the mobile check also asserts no horizontal page overflow.
Starlette emits an existing AnyIO alias deprecation warning. Initial sandbox
socket/subprocess failures were rerun with approved local access. E2E fixture
issues (reserved test email domain, stale selectors and full-suite rate limiting)
were corrected without weakening production authentication or request limits.

## Migrations and data protection

`0003_learning_challenges`, descending from `0002_hardware_jobs`, adds only
`challenge_workspaces`, `challenge_attempts`, their ownership indexes and unique
constraints. Completion derives from attempts; no duplicate completion table was
introduced. Existing Phase 2 exclusions of Alembic-owned tables from bootstrap and
the integer-ID legacy bridge were retained. No new recovery migration was needed.
Alembic's head is `0003_learning_challenges`; the older bootstrap marker in
`schema_migrations` remains separate from Alembic's revision tracking.

Verified fresh migration, repeated startup, upgrade/downgrade/re-upgrade, the full
integer-ID legacy entrypoint, and unchanged contents of existing model tables.
Downgrades were exercised only in disposable test schemas. The Phase 1 curriculum
bundle, Simulator V2 engine, freeform simulation API, quiz/progress APIs and saved
circuit models were not edited during recovery.

## Files

The complete uncommitted Phase 2 change set includes:

- Backend integration: `backend/app/main.py`, `backend/app/migrate.py`,
  `backend/app/legacy_migration.py`, `backend/app/models/__init__.py`.
- Backend feature: `backend/app/api/learning_challenges.py`,
  `backend/app/models/learning_challenge.py`,
  `backend/app/schemas/learning_challenge.py`,
  `backend/app/services/learning_challenges.py`, `backend/data/challenges.json`,
  `backend/migrations/versions/0003_learning_challenges.py`.
- Backend verification: `backend/scripts/export_challenge_contract.py`,
  `backend/tests/fixtures/learning_challenges.json`,
  `backend/tests/test_learning_challenges.py`, `backend/tests/test_hardware.py`.
- Frontend integration: `frontend/src/app/builder/page.tsx`,
  `frontend/src/app/learn/[id]/page.tsx`,
  `frontend/src/app/learn/components/Activities.tsx`,
  `frontend/src/components/circuit-builder/CircuitBuilder.tsx`.
- Frontend feature: `frontend/src/components/circuit-builder/ChallengePanel.tsx`,
  `frontend/src/components/circuit-builder/ChallengeFeedback.tsx`,
  `frontend/src/lib/learning-challenges.ts`.
- Frontend verification: `frontend/tests/learning-challenges.test.cjs`,
  `frontend/tests/fixtures/challenge-contract.json`,
  `frontend/tests/browser/learning-challenges.cjs`,
  `frontend/tests/browser/curriculum.cjs`.
- Documentation: `docs/CHALLENGE_SYSTEM.md`, `docs/PHASE2_RECOVERY_REPORT.md`.

Recovery specifically edited the validator service and API, challenge backend
tests, builder page/component, challenge panel/comparison/helper, frontend unit
tests, both curriculum/challenge browser scripts, and the two documentation files.
The remaining files retain the interrupted implementation.

## Commit status and limitations

No commit was created; all recovered work remains uncommitted for review. No
deployment or production migration was performed.
Temporary browser/API servers and the isolated PostgreSQL instance were stopped
after verification. Test data and logs were retained under `/tmp`.

Activity access requires authentication. Only committed work is persisted;
uncommitted edits are not autosaved. Activities are bounded to three qubits,
64 operations and 2048 shots, with a 200-attempt history cap per user/activity.
Teleportation uses a guided scaffold with exhaustive branch probes; conceptual
Shor activities are classical arithmetic, not a Shor quantum implementation.
Several advanced experiments/challenges intentionally share scaffolds. Live QPU
execution and external provider calls were not exercised.
