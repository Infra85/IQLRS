# IQLRS production deployment

The release preserves the UI-redesign design and the UUID models from `master`.
`main` was created from `master` because the repository had no main branch.

## Configure and launch

Use Node 22, Python 3.12, and PostgreSQL 16 or newer. Copy `.env.example` to an
ignored `.env`. Set `ENVIRONMENT=production`, a random `SECRET_KEY` of at least
32 characters, dedicated database credentials, SMTP credentials, `OPENAI_API_KEY`,
`AI_MODEL`, and `CORS_ORIGINS` to a JSON array of your exact HTTPS browser origins.
Production startup rejects missing credentials and unsafe defaults without printing
secret values. Obtain the AI model name from the models enabled for your account.

For a new Compose database, set `POSTGRES_PASSWORD` to a URL-safe random password.
Compose connects as `iqlrs`; do not attach a previously initialized `postgres`-user
volume expecting PostgreSQL environment variables to rename existing roles or
change existing passwords. For an existing database, use the native commands below
with its `DATABASE_URL` or adapt the Compose database settings to the existing role.

```bash
# Repository root; configure .env first.
docker compose build
docker compose up -d db
docker compose --profile tools run --rm migrate
docker compose up -d backend frontend
```

For the recommended VPS deployment, Caddy is included in Compose and terminates
HTTPS for `iqlrs.org`/`www.iqlrs.org`. Set `ACME_EMAIL` in `.env`, point Cloudflare
DNS records at the VPS public IP, and run `./deploy/update.sh`. Caddy obtains and
renews the origin certificate automatically. Keep Cloudflare SSL/TLS mode at
**Full (strict)**. Do not expose ports 3000, 8000, or 5432 publicly; Compose only
exposes 80/443 through Caddy.

Terminate HTTPS with your hosting platform or reverse proxy. Compose publishes
only the frontend on `127.0.0.1:3000`; backend and PostgreSQL stay on the private
network. Forward the public website to that port. Readiness is checked through
`/health/ready` inside the backend container. Never cache `/api/*` responses.

For native / managed database deployment:

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m app.migrate
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log

# In a separate process:
cd frontend
npm ci
# Set build environment or use frontend/.env.local from frontend/.env.example.
npm run build
PORT=3000 HOSTNAME=127.0.0.1 npm start
```

The frontend defaults to same-origin `/api`, proxied by Next.js. `API_PROXY_URL`
is a server-only **build-time** destination, defaulting to `http://127.0.0.1:8000`
for native development and `http://backend:8000` in Compose. To host the API on a
separate public domain, set `NEXT_PUBLIC_API_URL=https://api.your-domain` **before
building** and permit the exact frontend origin in `CORS_ORIGINS`. Rebuild when
these URLs change. Frontend builds do not read the repository root `.env` unless
Compose or your shell forwards it. No AI or SMTP secret belongs in frontend env.

Configure proxy client-IP forwarding only from trusted proxy addresses using
Uvicorn's `--forwarded-allow-ips`. If using Next.js as the proxy, the backend must
trust that private proxy address; its forwarded headers must be overwritten by
your public edge. Never trust arbitrary internet clients' forwarding headers.
Rate limits are shared in PostgreSQL; incorrectly configured client IP forwarding
can make all users share a limit. Set edge body-size limits (for example 64 KiB for
JSON APIs) and a proxy timeout above the AI provider's 45-second timeout plus retry.

## Migrations and existing data

`python -m app.migrate` is an idempotent, transaction-protected PostgreSQL migration
with an advisory lock and `schema_migrations` version record. It creates missing
UUID tables, widens OTP hashes, creates shared request counters, and seeds the
bundled curriculum using stable UUIDs. It never runs implicitly on application
startup. Run it once as a release job before accepting traffic.

For the original integer-ID schema it copies records into the UUID models with
deterministic primary/foreign-key mappings. Password hashes and verified flags
are preserved. Original tables, including columns absent from the new models,
remain in `<original_schema>_legacy_v1`, with public schema access revoked. Back up
with `pg_dump -Fc` and stop application writes before migrating. Keep that backup
off-host. If an unknown required field or inconsistent constraint is encountered,
the entire migration rolls back. Do not delete the archive until a separate data
retention review. The archive contains personal data and old credentials and must
remain restricted to administrators.

Old JWTs use integer subjects; users must sign in again after the migration.
Pending plaintext OTPs are invalidated and must be reissued. Email/password/name
values and existing account verification are retained. Built-in curriculum has a
non-login author record (`curriculum@iqlrs.invalid`, no password, unverified).
For rollback, stop writes and restore the pre-migration backup to a separate
PostgreSQL database, then point the previous application version to it. Do not
mix the UUID application with the integer-ID database.

## Email delivery

`RESEND_API_KEY` is the backend-only Resend HTTPS API key and `SMTP_EMAIL` is the
verified From address. Production requires both and uses Resend over HTTPS, so it
does not depend on Render's blocked outbound SMTP ports. `SMTP_USERNAME`,
`SMTP_PASSWORD`, and `SMTP_REPLY_TO` remain available for local/development SMTP
fallback; defaults use STARTTLS on Gmail port 587. TLS certificates are verified.

Messages identify IQLRS, explain the registration request, contain a plain-text
code and expiry, and include Date, Message-ID, an IQLRS display name, and an
Auto-Submitted header. No tracking pixels, attachments, marketing links, or fake
priority headers are added. Verification uses a JSON body, a keyed SHA-256 OTP
hash, ten-minute expiry, five failed attempts, a one-minute resend cooldown, and
shared request limits. Codes and SMTP provider error details are never logged.
Disable body capture/redact OTP/password fields in any external APM or proxy.

Publish Resend's SPF and DKIM records for the sending domain, with DKIM signing
enabled at the provider. Configure DMARC reporting and ensure the
visible From domain aligns with the authenticated SPF or DKIM domain. Start with
monitoring while checking legitimate senders, then adopt the appropriate enforced
policy. Use the provider's exact DNS values; do not publish multiple competing SPF
records. For a personal `@gmail.com` sender, Google controls these DNS records;
you cannot authenticate your own website domain by merely changing From.
Use a verified domain and transactional provider/Workspace setup for branded mail.
See [Google's sender guidelines](https://support.google.com/mail/answer/81126).

SMTP acceptance does not guarantee inbox placement. Check received-message
Authentication-Results for SPF/DKIM/DMARC, monitor bounces and complaints, and check
sender reputation. The application cannot guarantee that OTP mail avoids spam.
SMTP send and database commit cannot be atomic: if the database commit fails after
the provider accepts the email, registration must be retried.

## Feature availability and data

- Builder: Qiskit only; guests can experiment temporarily. Signed-in success saves
  Circuit, CircuitVersion, SimulationRun, and SimulationResult in one transaction.
  Failed writes return an error; no partial records are committed. Retrieval at
  `/api/circuits/runs/{uuid}` is restricted to the owner.
- Dashboard: real simulation/circuit counts, quiz average, completed lessons,
  recent activity, and an activity streak calculated using UTC dates. Empty
  accounts show zero and empty states. Quiz submission updates progress and
  course enrollment; repeated attempts do not duplicate completed modules.
- AI tutor: `/ai` uses private database conversations and the existing OpenAI
  Responses service. Input and history are bounded; messages save only after
  successful provider output. Backend missing-config and provider-error responses
  preserve the user's draft in the UI. There are no fake production responses.
  See [the OpenAI API quickstart](https://developers.openai.com/api/docs/quickstart).
- Code execution, instructor analytics, collaboration, Cirq/PennyLane runner
  stubs are unreleased. Editor/instructor routes return 404; their UI source is
  retained as `unreleased.tsx`. Stub code/collaboration APIs are not mounted.
- Narration retains neural speech and browser fallback. Speech quotas are
  process-local in the existing service; deploy one backend worker unless you add
  a shared provider budget at the edge. Other new request limits use PostgreSQL.

## Verification and maintenance

```bash
cd backend
TEST_DATABASE_URL=postgresql://... .venv/bin/python -m pytest tests -q
.venv/bin/ruff check app
.venv/bin/pip check
cd ../frontend
npm ci
npm run test
npm run lint
npm run build
npm audit --omit=dev
```

Tests create and remove isolated PostgreSQL schemas. Never point integration tests
at a database account without permission to create/drop those isolated schemas.
The production migration was verified on an isolated copy of the configured
legacy database; row counts and authentication data were checked. The original
configured database has not been modified. The protected local backup from this
session is `/tmp/iqlrs-production-backup/before-uuid.dump`; move a backup to durable
private storage before any real deployment migration.

Next.js was updated to 15.5.25 to address published security advisories; async route
parameters were adapted following [Next.js upgrade guidance](https://nextjs.org/docs/app/guides/upgrading/version-15).
Patched PostCSS/DOMPurify overrides are locked in package-lock.json. Backend direct
dependencies are pinned to tested versions, including bcrypt 4.0.1 for passlib
compatibility. Refresh locks and rerun audits regularly. The backend audit flags
`ecdsa 0.19.2` advisory `PYSEC-2026-1325` without a fixed version; this transitive
python-jose dependency is not used for the HS256-only JWT signing/verification
path. Do not enable ECDSA algorithms without reassessing that advisory.

Live provider prerequisites: the configured SMTP TLS/login check passed without
sending mail. Actual mailbox placement/DNS authentication was not tested. No
OpenAI key is configured locally, so live AI generation requires deployment
credentials; provider success/error contracts are covered with controlled test
responses, and missing configuration is checked through the real API and UI.
