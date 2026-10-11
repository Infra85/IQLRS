# IQLRS project instructions

## Start and resume every substantial task

1. Read this file, [HANDOFF.md](HANDOFF.md), and any more specific `AGENTS.md`
   governing files you will touch. User instructions take precedence.
2. Before proposing changes, inspect the actual repository state:

   ```bash
   git status --short --untracked-files=all
   git branch --show-current
   git branch -vv
   git log -10 --oneline
   git diff --stat
   git diff
   git diff --cached
   git ls-files --others --exclude-standard
   ```

   Read relevant untracked files too: `git diff` does not include their contents.
   Remote-tracking refs describe the last local fetch, not verified remote state.
3. Read the relevant existing documents below and inspect their implementation.
   Treat handoffs, completion claims, branch names and old test results as evidence
   to verify, not proof that the current tree is complete. Recover unfinished work
   before extending it. Classify uncertain work as done, partial, missing or broken
   and explain the evidence; do not restart an interrupted phase by default.
4. State the scope and preserve existing changes. Do not start a new phase merely
   because an old report recommends it. Resolve discrepancies against code, Git,
   dated verification evidence and the user's current task.

## Document ownership

- [HANDOFF.md](HANDOFF.md): the single concise, current session-resumption record.
  Keep active phase, branch, outstanding work and next action here, not in this file.
- [Original roadmap](docs/Architecture/roadmap.md): existing product ambitions and
  team plan; historical proposals are not implemented capabilities or authorization.
- [Architecture](docs/Architecture/architecture.md) and [README](README.md): overview;
  some sections describe the original design or the committed Phase 1 baseline.
- [Curriculum guidelines](docs/CURRICULUM_GUIDELINES.md) and
  [Phase 1 scientific review](docs/CURRICULUM_SCIENTIFIC_REVIEW.md): content conventions,
  stable identities, scientific evidence and safe bundle upgrades. Their Phase 1
  “planned activities” restriction describes that phase, not the later runtime.
- [Challenge system](docs/CHALLENGE_SYSTEM.md) and
  [Curriculum Phase 2 recovery report](docs/PHASE2_RECOVERY_REPORT.md): current activity
  contract, recovery audit, migration and detailed verification evidence.
- [Simulator V2](docs/SIMULATOR_V2.md) and its
  [Phase 1](docs/SIMULATOR_V2_PHASE1_REPORT.md),
  [Phase 2](docs/SIMULATOR_V2_PHASE2_REPORT.md),
  [Phase 3](docs/SIMULATOR_V2_PHASE3_REPORT.md) and
  [Phase 4](docs/SIMULATOR_V2_PHASE4_REPORT.md) reports: execution semantics and history.
  **Simulator V2 phase numbers and curriculum phase numbers are separate tracks.**
- [Deployment guide](docs/DEPLOYMENT.md) and
  [deployment verification](docs/DEPLOYMENT_REPORT.md): configuration and dated results.

Reuse these documents. Update the relevant contract when behavior changes; retain
historical results as dated evidence. Do not create parallel roadmaps, progress
logs or replacement phase reports for information already owned above.

## Repository and architecture

| Path | Responsibility |
|---|---|
| `frontend/src/app/` | Next.js App Router pages: lessons, builder, auth, dashboard, tutor |
| `frontend/src/components/circuit-builder/` | Existing editor, challenge panel, hardware UI and results |
| `frontend/src/lib/` | API/auth clients, editor helpers and frontend contracts |
| `frontend/tests/`, `frontend/tests/browser/` | Node tests and real-browser regressions |
| `backend/app/main.py`, `backend/app/api/` | FastAPI app and mounted HTTP routes |
| `backend/app/models/`, `backend/app/schemas/` | SQLAlchemy persistence and Pydantic request/response contracts |
| `backend/app/services/` | Curriculum, challenge validation, simulator and provider services |
| `backend/data/` | Canonical lesson bundle and companion activity definitions |
| `backend/app/migrate.py`, `backend/migrations/` | Transactional bootstrap/legacy migration and Alembic upgrades |
| `backend/tests/`, `backend/scripts/` | Scientific/integration tests, fixtures and contract export |
| `.github/workflows/ci.yml`, `deploy/`, `docker-compose.yml` | CI and deployment configuration |

The frontend uses Next.js/React/TypeScript and proxies `/api/*` to FastAPI through
`API_PROXY_URL` (default `http://127.0.0.1:8000`). PostgreSQL is accessed through
SQLAlchemy; authentication uses the existing bearer-token API. Do not infer Prisma
or NextAuth usage from historical plans or installed packages.

`backend/data/modules.json` is canonical. The curriculum service validates and
seeds it with stable UUID5 identities; lesson pages use the generated
`frontend/src/app/learn/modules.ts`. Activity definitions reuse those same module
and activity IDs. Server validators determine correctness; activity completion is
independent of quiz/module progress and derives from persisted successful attempts.

`CircuitRequest` is the shared circuit format. Quantum execution belongs in
`backend/app/services/simulators/engine.py`; `qiskit_runner.py` is the compatibility
entrypoint, not permission to add a second engine. Hardware providers have a
separate execution contract. Code Lab, instructor analytics and collaboration
remain unreleased unless later implementation and authorization establish otherwise.

## Constraints and Git conventions

- Never overwrite user edits, discard work, reset branches, or merge branches
  without explicit user authorization. Do not use `git reset --hard`, `git clean`,
  restore/revert, automatic stashing or a replacement checkout to make a dirty tree
  appear clean. Preserve unrelated work and inspect conflicts before editing.
- Existing topic branches use `feature/<topic>` or `feature/<topic>-phaseN`; `main`
  is the integration branch. Continue the verified active branch unless changing
  it is authorized. Do not switch branches with unfinished work merely for naming.
- Audit and test before any commit. Stage explicit paths only; do not sweep user
  work into a commit. Record commit/push/merge/deployment separately in the handoff;
  a request to implement or document is not permission to merge or deploy.
- Protect curriculum identities, Simulator V2 semantics, the freeform builder,
  quizzes, progress, saved circuits and historical assessment data. Reuse existing
  models, schemas, APIs, validators and components; inspect before adding equivalents.
- Preserve q0 as the least-significant qubit and displayed `q(n−1)…q0` ordering.
  Distinguish quantum controls from classical conditions, ideal probabilities from
  sampled counts, and a last-shot conditional statevector from an ensemble.
- Keep migrations additive and transactional where possible. Alembic-owned tables
  must not also be pre-created by bootstrap/legacy `create_all`. Exercise migration
  replay and preservation in disposable databases, never a learner/production DB.
- Never write credentials, tokens or real learner data into documentation or logs.
  Live QPU tests require explicit opt-in and can incur charges. Use the existing
  fake-provider fixture for ordinary hardware verification.

## Testing and local commands

Run from repository root unless marked otherwise. Check installed tools and
configuration first; `backend/.venv` is the existing local environment, not a
portable assumption. CI currently uses Python 3.12, Node 22 and PostgreSQL 16.

```bash
# TEST_DATABASE_URL must already point to a dedicated disposable PostgreSQL DB.
# Missing TEST_DATABASE_URL skips integration checks; that is not a full pass.
: "${TEST_DATABASE_URL:?Set a dedicated test database URL first}"
DATABASE_URL="$TEST_DATABASE_URL" backend/.venv/bin/python -m pytest backend/tests -q -rs
backend/.venv/bin/ruff check backend/app/
node frontend/scripts/sync-curriculum.cjs --check
git diff --check
```

From `frontend/`: `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`.
Use focused tests while editing, then required regression coverage for affected
behavior. For documentation-only work, validate links, commands, whitespace and
scope; do not present old application tests as fresh runs.

For authorized lesson edits, regenerate with
`node frontend/scripts/sync-curriculum.cjs`. For activity contract changes use
`PYTHONPATH=backend backend/.venv/bin/python backend/scripts/export_challenge_contract.py`
and inspect the generated fixture diff. Do not regenerate files just to resume.

On a confirmed disposable database, migration is
`DATABASE_URL="$TEST_DATABASE_URL" PYTHONPATH=backend backend/.venv/bin/python -m app.migrate`.
The local API starts with
`DATABASE_URL="$TEST_DATABASE_URL" PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`.
From `frontend/`, `npm run dev` starts development; after building,
`PORT=13002 HOSTNAME=127.0.0.1 npm run start` starts the browser-test production server.

Browser setup and exact scripts are maintained in
[Simulator verification](docs/SIMULATOR_V2.md#verification-commands),
[challenge testing](docs/CHALLENGE_SYSTEM.md#testing-and-manual-review) and
[hardware verification](docs/SIMULATOR_V2_PHASE4_REPORT.md#verification).
They need Playwright/Chrome, the real local API and an isolated learner where
authenticated. Honor rate limits. `/tmp` tools, tokens, servers and databases may
have disappeared after shutdown; verify or recreate only isolated test resources.

## Finish or pause every substantial task

Update [HANDOFF.md](HANDOFF.md) before the final response or planned stop. Record:

- Date, task/scope, active phase, actual branch and HEAD, relevant commits and dirty state.
- What was already present, what changed, and whether it is implemented, tested,
  committed, merged or deployed. Keep those states distinct.
- Exact validation commands or links to their maintained recipe, results/counts,
  skips/failures, environment and evidence locations. Label prior-session results
  as historical; missing logs or skipped tests are not verified success.
- Remaining tasks, blockers, unresolved decisions and known limitations; use
  “not run” or “unverified” when appropriate. Never infer completion from intent.
- One concrete next recommended action and any required authorization. Include
  test-service/resource state if it matters for resumption.

Keep the handoff concise by linking detailed reports. Do not erase unresolved work
when summarizing. Finally inspect Git status/diff, confirm only intended files were
changed, and tell the user how to resume. No workflow depends on chat memory alone.
