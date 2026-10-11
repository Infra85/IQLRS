# Current development handoff

Updated: 2026-10-11 (Asia/Kolkata). Read [AGENTS.md](AGENTS.md) first.

## Active task and Git state

Curriculum Phase 3 — interactive lesson engine — is implemented and locally
verified across all eight modules. Full factual report and 26-file inventory:
[PROJECT_STATE.md](docs/PROJECT_STATE.md). This is separate from Simulator V2 phases.

Branch `feature/learning-builder-integration`, HEAD `e645238`. Entry tree was clean.
The previous handoff was stale: Phase 2 was already committed at HEAD, not dirty.
Current changes: 18 modified tracked files and 8 new files, all Phase 3 work;
nothing staged. No commit, branch switch, merge, push, deployment or production
migration was performed. Remote state was not fetched. User explicitly prohibited
automatic commits; review authorization before any future Git publication action.

## What changed

Existing eight-module scientific curriculum, 16 activity definitions, validators,
quiz engine and simulator were reused. The metadata-derived journey adds reading
acknowledgements, reflection, explicit step states, resume, builder return paths,
prerequisite-aware next actions and a guided curriculum overview. Current immutable
attempt feedback restores on builder reload. Full guided completion is separate
from preserved legacy quiz progress; old successes and attempts remain intact.

Migration `0004_lesson_journey` adds nullable JSONB to existing `module_progress`.
No new grade or attempt persistence layer. It must run before deploying this app
version. See [the contract](docs/CHALLENGE_SYSTEM.md#guided-lesson-orchestration-phase-3)
and [deployment guide](docs/DEPLOYMENT.md). Shor remains conceptual.

## Verified this session

- Full backend: **633 passed, 2 skipped**, 42.16s. Skips are opt-in live QPU tests.
  `/tmp/iqlrs-journey-backend.log`.
- Focused journey suite, including added downgrade/dashboard assertions:
  **13 passed**, 9.26s; `/tmp/iqlrs-journey-focused.log`.
- Frontend: **48 passed**, no skips; typecheck, lint, production build passed.
  `/tmp/iqlrs-journey-frontend-tests.log`, `/tmp/iqlrs-journey-build.log`.
- Guided browser: **9 passed**, 60.52s — eight entire sequences, failed-save recovery,
  quiz retry, prediction resume after navigation, all 16 validated-activity reloads,
  and activity navigation while progress is loading. `/tmp/iqlrs-journey-e2e.log`.
- Existing challenge browser: **19 passed**, 81.40s; honored real 429 retry interval.
  `/tmp/iqlrs-journey-challenges-e2e.log`.
- Curriculum browser: 8 lessons, 24 answers/explanations, 8 quiz submissions/retries,
  16 activity links passed; `/tmp/iqlrs-journey-curriculum-e2e.log`.
- Freeform simulator browser passed all 21 operations, serialization, rotations,
  measurement/reset, labels and mobile layout; `/tmp/iqlrs-journey-simulator-e2e.log`.
- Migration: fresh, populated Phase 2 upgrade, repeat entrypoint, downgrade/re-upgrade,
  integer legacy upgrade and historical record preservation passed in disposable schemas.
- Ruff, curriculum sync check, whitespace, JS syntax and documentation links passed.
  Desktop/mobile screenshots visually reviewed; 390px overflow assertion passed.

Environment: local Python 3.14, Node 24.20.0, PostgreSQL 18.6 and system Chrome.
CI's older version matrix was not run locally. Existing lint/AnyIO deprecations
remain. Hardware and Simulator V2 phase 2/3 browser suites were not rerun; backend
regressions were included. Older verification stays in its original dated reports.
An initial SQL_ASCII disposable DB failed and rolled back; a new UTF-8 DB fixed the
setup. A real activity-link loading race was found, fixed and regression-tested.

## Reproduction and resource state

All test services are **stopped** (API 8000, frontend 13002, temporary PostgreSQL).
Disposable cluster `/tmp/iqlrs-journey-pg`, port 55439, DB `iqlrs_journey_utf8` retains
test data; `/tmp` artifacts may disappear. No existing learner DB was touched.
Playwright is under `/tmp/iqlrs-journey-browser`; private test account artifacts
must never be printed or copied into logs/docs.

Full backend command, from root:
```bash
TEST_DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_journey_utf8 \
DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_journey_utf8 \
backend/.venv/bin/python -m pytest backend/tests -q -rs
backend/.venv/bin/ruff check backend/app/
node frontend/scripts/sync-curriculum.cjs --check
git diff --check
```
Frontend commands from `frontend/`: `npm test`, `npm run typecheck`, `npm run lint`,
`npm run build`. Browser setup and exact entrypoints:
[verification recipe](docs/CHALLENGE_SYSTEM.md#phase-3-verification-recipe).
The full guided browser test requires a **fresh** isolated learner; the session's
learner completed all modules. The ephemeral `/tmp/iqlrs-journey-run.cjs` wrapper
privately loads a test token and runs a selected browser script.

## Remaining limits and next action

No known Phase 3 implementation blocker. Authentication is required for saved
progress. Reading/reflection completion is learner-acknowledged; prerequisites
are recommendations preserving direct URLs. Only committed builder work persists;
unsubmitted quiz answers and uncommitted edits are not autosaved. Activity size and
history limits are unchanged. No full Shor, Code Lab, new hardware, analytics,
collaboration or context-aware tutor work was added. Live hardware remains unverified.

**Next recommended action:** review the uncommitted Phase 3 diff and migration for
commit readiness on this branch. Start with the repository Git inspection and
PROJECT_STATE; do not redo completed implementation. Obtain explicit authorization
before committing, merging or deploying. No next development phase is authorized.
