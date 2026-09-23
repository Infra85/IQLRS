# Deployment verification — 2026-09-14

- **Merge:** `main` created from the repository's existing `master`; `UI-redesign`
  merged at `6512305`. Auth/dashboard conflicts resolved, then UUID contracts
  reconciled with the retained master models. No conflict markers remain.
- **Persistence:** authenticated Qiskit runs atomically save circuit, version,
  run, counts, probabilities, statevector, diagram, shots, backend and timestamps.
  Owner-only retrieval and failed-write rollback pass real PostgreSQL tests.
  Guest runs remain available and explicitly temporary.
- **Database:** fresh/idempotent migrations and legacy integer-to-UUID migration
  verified. A copy of the configured database preserved row counts, password
  hashes and verification flags. Original database remains unchanged; original
  tables are archived by the migration. Run the migration at deployment.
- **OTP/email:** hashes, JSON verification, expiry, cooldown, lockout and shared
  request limits tested. Provider TLS and SMTP login succeeded. Live delivery and
  spam placement were not tested. Configure SPF/DKIM/DMARC as described in
  [DEPLOYMENT.md](DEPLOYMENT.md); inbox placement cannot be guaranteed.
- **Dashboard:** persisted simulations, quiz scores, completed modules, course
  progress, UTC activity streak and recent activity; real actions update values.
- **AI:** authenticated tutor UI, private persisted history, bounded inputs,
  provider timeout/error handling, draft preservation. Provider contracts tested
  with controlled responses; real missing-key API/UI path verified. Live success
  requires `OPENAI_API_KEY` and an accessible `AI_MODEL`.
- **Unavailable modules:** code lab and instructor route entrypoints removed;
  source retained in `unreleased.tsx`. Stub code/collaboration APIs unmounted.
- **Frontend:** clean npm install, lint, unit tests, TypeScript and Next.js 15.5.25
  production build pass. Standalone startup and Docker image build pass. Dependency
  audit reports zero vulnerabilities with patched PostCSS/DOMPurify overrides.
- **Backend:** 50 PostgreSQL-backed/unit tests pass; Ruff and pip dependency checks
  pass. Python 3.12 production image builds and starts successfully. Real HTTP
  readiness, login, simulation/retrieval, dashboard and CORS checks pass.
- **Browser:** Chromium exercised login, OTP UI, simulation save, updated dashboard,
  lesson quiz, missing-AI-key behavior, unavailable routes and mobile navigation.
  No uncaught browser exceptions in that run.
- **Security/config:** production environment validation, non-root containers,
  private Compose database/API, same-origin API proxy, secret-safe configuration
  errors, no tracked credentials found by pattern scan. A transitive `ecdsa`
  advisory has no fix; HS256-only JWT code does not use ECDSA signing.

Changed areas: backend auth/circuit/progress/dashboard/AI APIs, email/security/
configuration, rate-limit model, migration/curriculum services, frontend auth,
API client, quiz/dashboard/builder/nav, new `/ai`, Docker/Compose/env templates,
CI and regression tests. The redesign's visual system is retained.

**Launch prerequisites:** supply production credentials (the local OpenAI key is
missing), configure HTTPS origins and sender-domain DNS, back up and run migrations.
Live AI access and actual mailbox delivery still need verification with deployment
provider credentials. This work does not push `main`, deploy a public service, or
change the remote default branch.
