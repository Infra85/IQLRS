# Project state — curriculum Phase 3

2026-10-11. Branch `feature/learning-builder-integration`, base HEAD `e645238`.
**Curriculum Phase 3 is implemented and locally verified across all eight modules.**
Changes are local and uncommitted; no merge, push, deployment or production
migration has occurred. [HANDOFF.md](../HANDOFF.md) owns session-resumption details.

## Audit and scope

The starting tree was clean. Phase 1 curriculum exists at `ae3ff38`; Phase 2
activities, tests and recovery are committed in `e645238`. The old handoff's claim
that Phase 2 was uncommitted was stale. This file did not exist on entry.
Simulator V2 Phases 1–4 are a separate track already present in local history.
No remote fetch was performed, so cached origin refs do not establish remote state.

| Area | Found | Phase 3 change |
|---|---|---|
| Scientific curriculum | Present: eight validated modules and stable identities | Unchanged |
| Activity engine | Present: 16 definitions, predictions, runs, comparison, validation, hints and immutable attempts | Reused; current attempt feedback also restored on reload |
| Lessons | Present: reusable content rendering, separate activity links and quiz | Guided sequence, reading acknowledgements, reflection and next-action controls |
| Quiz engine | Present: server grading and historical attempts | Reused; quiz pass remains distinct from full guided completion |
| Progress | Partial: legacy quiz/module percentage plus independent activity completion | Additive reading/cursor storage and server-derived full journey progress |
| Resume and navigation | Partial: committed builder workspace only | Per-module cursor, prerequisite-aware recommendation, builder return paths |

## Implemented behavior

All eight modules derive a nine-step sequence from existing metadata: objectives,
three concept sections, worked example, experiment, reflection, quiz, challenge.
Experiments contain the existing prediction → execution → comparison → feedback
workflow. Shor uses conceptual arithmetic and reasoning validation; it does not
run a Shor circuit. Authors' lesson and activity content is not rewritten.

Successful existing activity attempts and perfect historical quizzes count toward
the journey. Old quiz completion does **not** claim that unread sections or activities
were finished. Starting, running, validating, passing the quiz, acknowledging a
reflection and completing the full module remain distinct. All statuses have text
and symbols. Failed checks require retry; a new committed revision is in progress;
previous successes remain complete after a later failed retry.

Reading acknowledgements and the resume cursor use nullable JSONB on the existing
`module_progress` model. `0004_lesson_journey` adds that column and preserves all
legacy fields. Full journey completion is derived, not a second grade or duplicate
attempt table. Migration is transactional through the existing entrypoint and must
run before deploying this application version. Detailed contract and verification
recipe: [challenge system](CHALLENGE_SYSTEM.md#guided-lesson-orchestration-phase-3).

## Verification

All checks below used the local Python 3.14 virtualenv, Node 24.20.0,
PostgreSQL 18.6 and system Chrome. CI's Python 3.12 / Node 22 / PostgreSQL 16 matrix
was not run locally. The API used a dedicated UTF-8 disposable database at port
55439; browser tests used a production Next.js build at port 13002 and isolated
learners. No real learner data or hardware provider calls were involved.

| Check | Result / evidence |
|---|---|
| Full backend `TEST_DATABASE_URL=… DATABASE_URL=… backend/.venv/bin/python -m pytest backend/tests -q -rs` | **633 passed, 2 skipped**, 42.16s; `/tmp/iqlrs-journey-backend.log` |
| Focused journey suite after extra downgrade/dashboard assertions | **13 passed**, 9.26s; `/tmp/iqlrs-journey-focused.log` |
| Frontend `npm test` | **48 passed**, no skips |
| Frontend `npm run typecheck`, `npm run lint`, `npm run build` | Passed; `/tmp/iqlrs-journey-build.log` |
| `backend/.venv/bin/ruff check backend/app/` | Passed |
| `node frontend/scripts/sync-curriculum.cjs --check` | Passed; canonical curriculum unchanged |
| Full guided browser `frontend/tests/browser/lesson-journey.cjs` | **9 passed**, no skips, 60.52s; all eight complete sequences plus loading-link regression; `/tmp/iqlrs-journey-e2e.log` |
| Existing challenge browser | **19 passed**, no skips, 81.40s; `/tmp/iqlrs-journey-challenges-e2e.log` |
| Existing curriculum browser | Passed: 8 lessons, 24 answers/explanations, 8 quiz submissions/retries, 16 activity links; `/tmp/iqlrs-journey-curriculum-e2e.log` |
| Freeform `frontend/tests/browser/simulator-v2.cjs` | Passed: all 21 operations, serialization, rotations, measurement/reset, labels, mobile layout; `/tmp/iqlrs-journey-simulator-e2e.log` |
| Migration checks | Fresh migration, populated Phase 2 upgrade, replay, downgrade/re-upgrade, integer legacy upgrade and historical data preservation passed in disposable schemas |

The two skips require explicit live-QPU opt-in. Hardware browser suites and
Simulator V2 phase 2/3 browser scripts were not rerun for this orchestration change;
their backend regressions passed in the full suite. Historical results remain in
their original reports. Existing Next lint and Starlette/AnyIO deprecation warnings
remain. `git diff --check`, JavaScript syntax and local documentation links/anchors passed.

The initial ASCII test database could not store scientific Unicode and its migration
rolled back. A new UTF-8 disposable DB resolved the environment issue. Initial
sandbox socket/subprocess failures were rerun with approved local access. Existing
challenge E2E exposed a real race when clicking an activity before progress loaded;
the link now falls back to normal navigation until its context is ready. The new
browser regression holds that response pending and verifies navigation. The fixed
existing challenge suite also passed; it honored a 60-second API rate-limit retry. Browser
tests also cover failed-save recovery, quiz retry, prediction resume after navigation,
reload of all 16 activities including feedback, and non-color completion states.

Desktop curriculum and mobile journey screenshots were visually inspected. The
browser test asserts no overflow at 390px. Evidence: `/tmp/iqlrs-journey-complete.png`,
`/tmp/iqlrs-journey-mobile-panel.png`, `/tmp/iqlrs-journey-dashboard.png` (ephemeral).
Exact setup and commands: [verification recipe](CHALLENGE_SYSTEM.md#phase-3-verification-recipe).

## Changed files

- Backend: `backend/app/services/lesson_journey.py`, `backend/app/api/progress.py`,
  `backend/app/api/dashboard.py`, `backend/app/api/learning_challenges.py`,
  `backend/app/models/learning.py`, `backend/migrations/versions/0004_lesson_journey.py`.
- Frontend orchestration: `frontend/src/app/learn/components/LessonJourney.tsx`,
  `frontend/src/lib/lesson-journey.ts`, `frontend/src/app/learn/[id]/page.tsx`,
  `frontend/src/app/learn/components/Activities.tsx`,
  `frontend/src/app/learn/components/Quiz.tsx`, `frontend/src/app/learn/page.tsx`,
  `frontend/src/app/dashboard/page.tsx`.
- Builder restoration: `frontend/src/components/circuit-builder/ChallengePanel.tsx`,
  `frontend/src/lib/learning-challenges.ts`.
- Tests: `backend/tests/test_lesson_journey.py`, `backend/tests/test_learning_challenges.py`,
  `frontend/tests/lesson-journey.test.cjs`, `frontend/tests/browser/lesson-journey.cjs`,
  `frontend/tests/browser/learning-challenges.cjs`, `frontend/tests/browser/curriculum.cjs`.
- Documentation: `README.md`, `docs/CHALLENGE_SYSTEM.md`, `docs/DEPLOYMENT.md`,
  this file, and `HANDOFF.md`.

## Boundaries and limitations

- Guided progress requires authentication. Public lessons and quiz previews remain
  accessible; activity execution continues to require sign-in.
- Reading and reflection completion are explicit learner acknowledgements, not
  automatically assessed comprehension. Reflection is gated on a successful experiment.
- Prerequisites guide recommended ordering and next-module links; existing URLs
  remain accessible for preview, review and backward compatibility.
- Only committed activity work persists. Unsubmitted quiz answers and uncommitted
  circuit/prediction edits are not autosaved. Saved grades and successful attempts
  survive navigation and reload.
- Reading keys use existing section anchors scoped to `curriculumVersion`; an author
  changing section identities must bump that version. Historical grades are retained.
- Existing activity limits and the 200-attempt cap are unchanged. No Code Lab,
  simulator replacement, hardware expansion, instructor analytics, collaboration or
  context-aware tutor was added. Live hardware is unverified.

## Delivery and next action

No known Phase 3 implementation blocker remains. The 26-file change set is unstaged
and uncommitted on the original branch. No curriculum content, simulator engine or
challenge grading rules changed. No merge, push, deployment, production migration
or live-QPU test occurred. Local test services were stopped; disposable DB data and
logs remain under `/tmp` and may disappear on restart.

Next: review this diff and the migration contract for an explicitly authorized
commit/release. Resume from [HANDOFF.md](../HANDOFF.md); do not infer permission to
commit, merge or deploy from local verification.
