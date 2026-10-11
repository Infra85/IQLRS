# Current development handoff

Updated: 2026-10-09 (Asia/Kolkata). Read [AGENTS.md](AGENTS.md) first, then verify
Git and the files below; this snapshot is not proof of a future checkout's state.

## Active work and Git state

- **Active phase:** curriculum Phase 2 — learning/builder integration, recovered
  and tested but **uncommitted**. No next development phase has been started.
- **Current task:** establish repository context and session-resumption instructions;
  documentation only, adding `AGENTS.md` and this file.
- **Branch:** `feature/learning-builder-integration`; no configured upstream shown
  by `git branch -vv` at this audit.
- **HEAD:** `ae3ff38` — `feat(curriculum): complete scientific content and validation pass`.
  `feature/curriculum-scientific-pass` points to the same commit.
- **Integration baseline:** local `main` and cached `origin/main` point to `f83b108`
  (Simulator V2 Phase 4 merge). Earlier merges: `18a90ef` (debugging), `83717d8`
  (classical execution), `f08d07c` (gates/measurement/reset). Remote state was not fetched.
- **Dirty state on entry:** 9 modified tracked files + 18 untracked files = 27
  Phase 2 files. This task adds two untracked documentation files, for 29 total.
  No staged changes, new commit, branch operation, merge, push or deployment.
  Use `git status --short --untracked-files=all`; untracked feature files are essential.

## Completed work and existing documentation

Phase 1 curriculum is committed. Simulator V2 Phases 1–4 are in `main`'s history.
These are separate phase tracks. Curriculum Phase 2 already supplies all 16
activities, authenticated prediction/run/validation/hint/history APIs, immutable
attempts and independent completion, builder integration, and migration
`0003_learning_challenges` (two additive tables; no production migration performed).
Recovery fixed register-mismatch feedback, version replay, shot/input limits,
context navigation and comparison outcomes, and expanded preservation/E2E tests.

Reuse these sources rather than creating another plan or progress document:

- [Original roadmap](docs/Architecture/roadmap.md): historical product/team plan.
- [Phase 1 review](docs/CURRICULUM_SCIENTIFIC_REVIEW.md) and
  [authoring guidelines](docs/CURRICULUM_GUIDELINES.md): scientific/content contract.
- [Challenge system](docs/CHALLENGE_SYSTEM.md): Phase 2 architecture and operating contract.
- [Phase 2 recovery report](docs/PHASE2_RECOVERY_REPORT.md): full area-by-area audit,
  recovery changes, 27-file inventory, migration evidence and limitations.
- [Simulator V2](docs/SIMULATOR_V2.md) and the Phase 1–4 reports linked from
  [AGENTS.md](AGENTS.md): execution history; their old “next phase” advice is historical.
- [Deployment guide](docs/DEPLOYMENT.md): release configuration and prerequisites.

No separate current curriculum Phase 3 plan was found. README and some architecture/
authoring prose still describe the committed Phase 1 “planned activities” state;
the uncommitted Phase 2 contract/report explain the newer runtime. This setup
preserves those documents rather than rewriting historical scope or claiming release.

## Verification evidence

**Prior recovery run, 2026-10-09 — not rerun during this documentation task:**

| Check | Recorded result |
|---|---|
| Full backend `python -m pytest backend/tests -q -rs` with isolated PostgreSQL | 620 passed, 2 skipped; includes 67 challenge tests |
| Frontend `npm test` | 45 passed |
| Frontend typecheck, lint, production build; backend Ruff | Passed |
| Challenge browser | 19 passed; all 16 activities plus recovery regressions |
| Curriculum browser | 8 lessons/quizzes, 24 answers/explanations, 16 activity links passed |
| Simulator browser Phases 1–3; hardware disabled/enabled fixture | Passed |
| Migration preservation/replay | Passed in isolated databases; detailed report linked above |

The two skips are opt-in live QPU tests; real hardware remains unverified.
Recovery used `/tmp/iqlrs-recovery-pg`, port 55439, database `iqlrs_recovery`, a
dedicated learner, and the production frontend on port 13002. Services were stopped
after verification. Do not assume they or the `/tmp` artifacts survive a reboot.

The setup audit re-read available `/tmp/iqlrs-recovery-backend-final.log`,
`/tmp/iqlrs-recovery-build-final.log`, challenge/curriculum/simulator and hardware
E2E logs, corroborating the report. Frontend unit/typecheck/lint and Ruff results
are retained in the dated recovery report and prior run output, not new executions.
Reproduction commands live in [AGENTS.md](AGENTS.md) and the linked feature guides.

**This documentation task:** passed `git diff --check` and an inline Python audit
of all 30 relative links/anchors, Markdown fences/whitespace, shell-block syntax
(`bash -n`), referenced tools/paths and npm script names. A before/after SHA-256
comparison confirmed all 225 pre-existing repository files unchanged, with only
`AGENTS.md` and `HANDOFF.md` added; branch, HEAD and index also unchanged. The local
comparison manifest is `/tmp/iqlrs-context-setup-baseline.json` (ephemeral).
Application tests/build were not rerun: no application code changed in this task.

## Outstanding tasks, blockers and next action

- No known implementation blocker is recorded by the recovery audit. The feature
  and new workflow files remain local and uncommitted; Git has not durably recorded them.
- Before release, reconcile current feature-status prose in existing overview docs
  as part of an authorized Phase 2 review. No deployment or live-provider acceptance
  is evidenced by local tests. Do not treat these as permission to start another phase.
- Known feature limits: authenticated activities, committed-state persistence only,
  bounded circuits/history, guided teleportation and conceptual Shor arithmetic.
  See the recovery report for exact limits; these are not promised unfinished features.

**Exact next recommended action:** perform a read-only Phase 2 pre-commit review on
the current branch: run the startup Git inspection in `AGENTS.md`, read the challenge
contract/recovery report and every relevant tracked/untracked diff, and reconcile
them with this handoff. Verify any new changes with the appropriate tests. Then
report readiness for an explicitly scoped commit; do not stage, commit, switch or
merge branches, deploy, or begin a new phase as part of resuming that review.

Suggested next request: “Read AGENTS.md and HANDOFF.md, verify the working tree,
and review the recovered curriculum Phase 2 changes for commit readiness. Preserve
all existing work; do not commit or start another phase.”
