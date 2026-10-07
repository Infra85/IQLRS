# Simulator V2 Phase 4 — Actual Quantum Hardware Execution

## Delivery and verification boundary

Branch: `feature/simulator-v2-phase4-hardware`, created from Phase 3 commit
`4b7ef5c4e32c7c13bd853063e5fff6fdf268a5c0`. No changes are made to the Phase 1–3
or `main` branch references. Local simulator mathematics and trace implementation
are unchanged.

IBM Quantum and Amazon Braket QPU adapters are implemented. Hardware is disabled
by default. Their SDK translation paths, provider contracts, authenticated API,
PostgreSQL persistence, and production browser workflows are tested without
provider credentials. **No live QPU job was submitted or retrieved in this
environment.** Neither IBM credentials nor Braket region/result-bucket/account
configuration was present. This report does not certify live account access,
current device availability, or acceptance by any particular QPU.

The browser fixture runs the real API, authentication, rate limits, and database;
it substitutes only the remote provider boundary. Fixture counts are test data,
not evidence of a hardware execution. The fixture is under `backend/tests` and
is never imported by the deployed application.

## Architecture

One IQLRS `CircuitRequest` feeds either the existing local engine or a hardware
adapter. `HardwareProvider` defines discovery/device lookup, compilation,
submission, status, results, and cancellation. Compilation performs capability
validation and returns a provider object privately plus a serializable summary.

- `services/hardware/base.py`: contracts, canonical measurement projection,
  shared circuit validation, result integrity, safe error categories.
- `ibm.py`: IBM authentication, backend targets, Qiskit construction/transpilation,
  client-side Sampler, RuntimeJob recovery, status and register parsing.
- `braket.py`: AWS authentication/session, QPU discovery, capability inspection,
  OpenQASM serialization, asynchronous tasks and measurement-qubit projection.
- `registry.py`: lazy optional dependency/configuration detection.
- `api/hardware.py`: provider-neutral ownership, limits, reservations, lifecycle,
  and sanitized responses. No SDK calls or local simulator fallback.
- `models/hardware.py`: dedicated durable `HardwareJob` table.
- `HardwareExecution.tsx`: target selection, preview, confirmation, job polling,
  measured distributions, history, and optional local comparison.

There are no direct IonQ, IQM, Rigetti, Quantinuum, D-Wave or Azure integrations.
Braket vendors are discovered through its SDK. A discovered QPU is usable only
when its action format and capabilities satisfy the submitted circuit.
Analog-only devices can be visible as QPUs but fail gate-model validation.

## Dependencies and upstream API inspection

Inspected development runtime: Python **3.14.7**, Qiskit **2.5.2**, FastAPI
**0.141.1**, Pydantic **2.13.5**, SQLAlchemy **2.0.52**. Cloud SDKs were initially
absent. Dependency resolution and installation succeeded without changing these
versions; `pip check` reported no broken requirements.

Optional manifests pin:

- `backend/requirements-hardware-ibm.txt`: `qiskit-ibm-runtime==0.50.0`.
- `backend/requirements-hardware-braket.txt`: `amazon-braket-sdk==1.127.3.post0`.
- Core requirements add `alembic==1.18.4` for durable schema evolution.

The IBM adapter imports `qiskit_ibm_runtime.executor_sampler.Sampler`. It does
not use the legacy server-side Sampler import. The installed SDK's executor
result decoder restores Sampler register data from a recovered RuntimeJob,
including after process restart. Error mitigation/twirling is not enabled.
See [IBM's current client-side Sampler API](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/executor-sampler-sampler)
and [RuntimeJobV2](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/runtime-job-v2).

Braket uses `AwsDevice.get_devices(types=["QPU"])`, device properties, queue
metadata, `AwsSession.create_quantum_task`, and `AwsQuantumTask`. Direct SDK
service submission is intentional: `AwsDevice.run` does not forward arbitrary
`clientToken` kwargs to task creation. Calling the service method lets IQLRS
supply its stable UUID as AWS's idempotency token. See
[AwsDevice](https://amazon-braket-sdk-python.readthedocs.io/en/stable/_apidoc/braket.aws.aws_device.html),
[AwsQuantumTask](https://amazon-braket-sdk-python.readthedocs.io/en/stable/_apidoc/braket.aws.aws_quantum_task.html),
and [GetDevice metadata](https://docs.aws.amazon.com/braket/latest/APIReference/API_GetDevice.html).

The Braket SDK itself transitively installs its default simulator package; IQLRS
never imports or selects it as a hardware execution target. These optional
manifests are not installed in default deployment images.

## Operator deployment

Install the core requirements, then only the desired optional SDK manifests:

```bash
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/pip install -r backend/requirements-hardware-ibm.txt
backend/.venv/bin/pip install -r backend/requirements-hardware-braket.txt
PYTHONPATH=backend backend/.venv/bin/python -m app.migrate
```

Set credentials using backend environment/secrets management. Never put tokens
in frontend environment variables, circuit JSON, database records or logs.

| Variable | Default / purpose |
| --- | --- |
| `HARDWARE_EXECUTION_ENABLED` | `false`; explicitly enable real hardware |
| `HARDWARE_MAX_SHOTS` | `1024` per single-circuit job |
| `HARDWARE_MAX_JOBS_PER_USER_PER_DAY` | `5` reservations per user, UTC day |
| `HARDWARE_MAX_SHOTS_PER_USER_PER_DAY` | `4096` reserved shots per user, UTC day |
| `IBM_QUANTUM_TOKEN` | Backend-only IBM platform API key |
| `IBM_QUANTUM_INSTANCE` | IBM Cloud instance CRN authorized for Quantum Compute |
| `BRAKET_REGION` | AWS region used for discovery/session initialization |
| `BRAKET_S3_BUCKET` | Existing, operator-owned result bucket |
| `BRAKET_S3_PREFIX` | `iqlrs-hardware`; result object prefix |
| `HARDWARE_IBM` / `HARDWARE_BRAKET` | Docker build arguments, default `false`, install optional SDKs |

IBM uses `channel="ibm_quantum_platform"`, explicit token and instance. It does
not persist an SDK account file or accept a client-specified endpoint. Discovery
uses hardware backends and returns operational state, target operation names,
qubit count, coupling edges and backend pending jobs. Pending jobs are a backend
queue depth, **not** a guaranteed position or wait time for the user's job.

AWS uses Boto3's standard credential chain: prefer workload roles; named profiles
or `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` are also
supported. Those variables are read by AWS, not exposed through application
settings endpoints. Configure the SDK credentials/role in the backend process or
container. `BRAKET_REGION` and the S3 bucket alone do not confer access. Grant
least-privilege Braket discovery, Get/Create/CancelQuantumTask and result-bucket
access (including required S3 encryption permissions); device/account/provider
onboarding must already be complete. QPU tasks use their ARN's region for recovery.
AWS credentials are resolved and authenticated through STS during lazy initialization; actual Braket permissions
and device availability are checked by discovery and provider operations.

Docker Compose passes optional installation build arguments to the backend;
rebuild after enabling them. The migration image needs core dependencies only.
Both images include the Alembic revision. Existing startup remains
`python -m app.migrate`, followed by Uvicorn. Hardware-enabled readiness also
checks the hardware table. Never mount SDK credentials into the frontend.

With the flag off, registry construction stops before SDK imports, discovery
reports disabled, and submission controls are absent. Missing SDKs or credentials
are reported per provider without breaking local simulation. After changing
provider credentials/configuration, restart API workers to rebuild cached clients.

## API and lifecycle

All device/job routes require authentication. Provider availability is a bounded
public status response containing no credentials.

| Route under `/api/hardware` | Behavior |
| --- | --- |
| `GET /providers` | Flag, configured/available provider states, shot ceiling |
| `GET /devices?provider_id=ibm&operational_only=true` | Dynamic hardware-only discovery |
| `GET /devices/{provider_id}/{device_id:path}` | Exact discovered backend/ARN lookup |
| `POST /jobs/validate` | Validate and compile; never submit |
| `POST /jobs` | Requires `confirmed: true` and `Idempotency-Key`; returns HTTP 202 |
| `GET /jobs` | Owner's most recent 20 persistent jobs |
| `GET /jobs/{uuid}` | Owner-scoped status refresh, bounded provider polling |
| `GET /jobs/{uuid}/result` | Completed result, otherwise HTTP 409 |
| `POST /jobs/{uuid}/cancel` | Calls provider cancellation; records request only |

Validation/submission accepts `execution_mode: "HARDWARE"`, provider, device ID,
and the existing circuit object (including its shot count). Batch submissions
are intentionally not accepted: **one circuit per job**. Extra outer fields and
non-boolean confirmation are rejected. Shared normalization checks qubit indices,
gate parameters, destinations and conditions. Unresolved/non-finite angles fail.
Circuit limits remain 10 qubits, 500 operations, eight registers and 32 classical
bits, with a 128 KiB serialized hardware-circuit ceiling. Hardware rejects local
seed, shot-history and enabled debug options.

Submission validates/compiles before reserving a job. A database owner-row lock
serializes quota accounting and idempotency across workers; a unique owner/key
constraint is a second guard. Reservations commit **before** invoking the remote
SDK. A reused key with the same workload returns the same internal job; different
payloads receive HTTP 409. Reservation records are retained with the job, rather
than expiring into an opportunity for an accidental duplicate charge.

The POST waits for compilation and provider acceptance, never QPU completion.
A definite provider rejection becomes `FAILED`; an ambiguous timeout/crash stays
`UNKNOWN`, with a warning not to resubmit under a new key. No automatic paid-job
retry occurs. AWS additionally receives a stable client token; IBM receives an
internal-ID job tag. If a process dies after IBM accepts a job but before its ID
is committed, an operator must reconcile that tag with the provider console.
There is no unattended reconciliation worker in this phase.

Browser polling starts at five seconds and backs off to 30 seconds. It stops at
`COMPLETED`, `FAILED`, or `CANCELED`. Server row locking and a five-second refresh
floor coalesce duplicate polls. Results are fetched only after the provider says
the job is complete, with a bounded SDK result wait. Transient retrieval errors
leave the job retryable; complete counts must pass integrity checks before the
application records `COMPLETED`. Jobs survive restarts; status reconciliation is
on access, so completion timestamps represent when IQLRS observed completion.

| IBM status | IQLRS status |
| --- | --- |
| INITIALIZING | VALIDATING |
| QUEUED / RUNNING | QUEUED / RUNNING |
| DONE | COMPLETED |
| ERROR | FAILED |
| CANCELLED | CANCELED |

| Braket status | IQLRS status |
| --- | --- |
| CREATED | VALIDATING |
| QUEUED / RUNNING / COMPLETED / FAILED | Same normalized state |
| CANCELLING | CANCEL_REQUESTED |
| CANCELLED | CANCELED |

Unknown provider values map to `UNKNOWN`; the original status is metadata.
Cancellation invokes the actual provider. `CANCEL_REQUESTED` does not claim that
execution stopped. A later status may still be `COMPLETED` if cancellation lost
the race. Unsupported terminal/uncertain states receive a clear conflict error.

## Capability validation and compilation

**IBM:** construct a Qiskit circuit with named classical registers, measurement
destinations, reset and numeric gates. Controlled gates use Qiskit's controlled
instructions; equality conditions use `if_test`. Dynamic behavior is allowed only
when the selected target advertises `if_else`; reset also requires target reset
support. The target transpiler can reject additional combinations. Conditional
measurement writes are rejected because SDK final memory cannot report IQLRS's
`x` marker for a skipped write faithfully.

Transpile against the actual backend, optimization level 1, fixed transpiler seed
42. Hardware connectivity and basis are not hardcoded. Preview reports original
operation count, translated depth, compiled instruction count/depth, physical
qubit width, classical bit mapping and native operation names. Routing-only counts
are `null`: a gate-count increase also includes decomposition and cannot honestly
be labeled inserted routing. Qiskit may allocate the full physical target width.

**Braket:** accept gate-model OpenQASM devices and exact SDK operations listed by
the device, including rotations when advertised. Translate one-control X/Y/Z,
SWAP and supported single-qubit operations. Multi-control variants and other
unimplemented controlled gates are rejected. All reset, mid-circuit measurement
and conditional execution are conservatively rejected by this adapter, even if a
future device advertises support. These are adapter limitations, not claims that
all Braket QPUs lack those capabilities.

Terminal measurements map source qubits to named IQLRS classical destinations.
Repeated terminal reads are projected from the same sampled qubit. Action flags
requiring all used qubits to be measured or contiguous indices are enforced.
The provider handles exact OpenQASM decomposition and virtual-to-physical routing;
IQLRS does not claim a native physical schedule preview. Braket preview depth is
the translated circuit depth, and its warnings explain that final physical depth
and routing are unavailable before submission. Availability windows and queue
metadata are displayed when provided; permission failures on optional queue
queries yield unavailable information, never fabricated positions or times.

Unsupported semantics are rejected. There is no operation deletion to make a
unitary circuit run, local emulation, local noise simulation, automatic error
correction, mitigation, or simulator fallback.

## Canonical result convention

`execution_mode` is `HARDWARE`. The response includes internal/provider IDs,
provider/device, normalized status, shots, timestamps, compilation/queue metadata,
failures and normalized counts. SDK objects are never returned or stored.

The canonical bit order is **register declaration order, descending bit index
within each register, projected onto measured destinations**. An explicit
`classical_bit_order` accompanies the counts. A legacy circuit without explicit
classical mappings receives the same final full readout as the simulator:
`q[n-1] ... q[0]`, with `q0` rightmost. Thus X on q0 of a two-qubit circuit gives
`01`, not `10`. Local classical and legacy result semantics are unchanged. Local responses now explicitly
include `execution_mode: LOCAL_SIMULATION`; the local endpoint rejects a request
marked `HARDWARE` instead of ignoring that field. Hardware circuit requests use
the hardware variant of the shared circuit schema.

IBM register bitstrings are already high-bit first. The adapter joins individual
register samples by the **same shot index**, then projects the canonical order;
it never multiplies marginal register histograms. It verifies register widths and
sample counts. Braket bitstrings follow `measured_qubits`; the adapter maps each
canonical destination through that list explicitly. Both paths reject malformed
bits, negative/non-integer counts, wrong widths and shot totals. Complete results
must satisfy `sum(counts.values()) == shots`; partial results are not presented
as complete. No statevector or internal checkpoint is manufactured.

## Persistence, security and workload controls

The dedicated Alembic revision `0002_hardware_jobs` bridges the existing version-1
bootstrap. The old migration entrypoint still bootstraps local tables and invokes
Alembic for hardware. Upgrade, repeat upgrade and downgrade are tested. Job rows
store UUID ownership, idempotency/fingerprint, provider IDs, circuit snapshot,
shots/status, UTC timestamps, bounded compilation/results and safe failure text.
They contain no tokens, raw SDK objects, unbounded provider history or debug traces.

Hardware request scopes are independent of local simulation:

- Submission: 5 requests/minute/IP; daily user job and shot budgets also apply.
- Validation: 10/minute/IP; discovery: 12/minute/IP.
- Status/history/results share 30/minute/IP; provider availability: 60/minute/IP.
- Cancellation: 5/minute/IP.

These reuse PostgreSQL-backed rate counters, not per-process memory. The existing
trusted-proxy policy controls client-IP attribution. Daily quotas count all
reserved jobs, including ambiguous/failed ones; failed validation does not reserve
quota. Users cannot increase server/provider shot ceilings from the browser.

Owner filtering applies to details, history, results and cancellation; other
users receive 404 even if they know the UUID. Device input is matched against
provider discovery before SDK lookup; no client-specified URLs or S3 destinations
are accepted. Browser credentials only authorize IQLRS, not cloud providers.
Errors map allowlisted codes/types to authentication, quota, rate, compilation,
cancellation-state or timeout messages. Raw SDK messages and stack traces are not
logged because they can contain secrets. Audit events retain owner/job references,
provider/device/shots, workload fingerprint, provider ID and state, plus safe
exception types for diagnosis.

A pre-existing credential-shaped OpenAI value was removed from `.env.example`.
No comparable credential patterns remained in the tracked current files checked.
Historical commits were not rewritten: if the old value is genuine, the operator
must revoke/rotate it. Pattern scanning is not proof that no secret exists in
all history or external configuration.

## Frontend

The existing builder gains a small execution-target/job panel. Local execution
retains existing controls and results. Hardware mode hides local Run, debug and
seed/history controls. Validation and a review dialog precede paid submission;
the dialog shows provider, device, circuit qubits, shots, queue information,
compilation behavior, unsupported-operation policy and quota/charge notice.
Changing the circuit/target invalidates the previous preview.

Saved jobs come from the authenticated backend after refresh. The job panel
shows IDs, status, queue, safe errors and cancellation. Hardware results are
labeled **REAL HARDWARE RESULT**. Optional comparison executes the persisted
submitted circuit locally, up to 256 shots, and compares percentages. It does not
compare against an edited builder circuit or claim that deviations indicate a
simulator bug. Noise, routing, calibration, gate and readout effects are explained.

## Verification

Backend result: **473 passed, 2 skipped**, one existing Starlette/AnyIO deprecation
warning. The two skipped tests are the opt-in IBM/Braket paid QPU smoke tests.
Offline tests cover SDK translation, discovery/filtering, operational capabilities,
status mappings, cancellation, asymmetric bit ordering, correlated registers,
invalid counts, no-submit validation, ownership, safe errors, quotas/rate limits,
concurrent idempotency, uncertain submission, persistence and migration rollback.

Frontend: six test files passed; lint, typecheck and production build passed.
All Phase 1, Phase 2 and Phase 3 production browser suites passed against the
actual local API. The Phase 4 disabled-mode browser check passed. The enabled Phase 4 browser suite passed discovery, validation without submission,
confirmation, queued/running/completed states, results, comparison, refresh, failure,
ownership, idempotency and mobile layout. The remote QPU boundary was a fixture.
SDK `pip check`, Ruff and `git diff --check` passed.

Exact verification commands (from repository root unless stated):

```bash
TEST_DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check backend/.venv/bin/python -m pytest backend/tests -q
backend/.venv/bin/ruff check backend/app/
backend/.venv/bin/pip check
git diff --check
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2.cjs
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase2.cjs
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase3.cjs
HARDWARE_BROWSER_DISABLED=true NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase4.cjs
NODE_PATH=/tmp/iqlrs-browser-check/node_modules node frontend/tests/browser/simulator-v2-phase4.cjs
cd frontend
npm test
npm run lint
npm run typecheck
npm run build
```

Browser server setup: migrate the isolated database, run
`DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`
and `PORT=13002 npm run start` in `frontend`. For the enabled fixture suite only,
replace the API process with
`DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_check PYTHONPATH=backend:backend/tests backend/.venv/bin/uvicorn hardware_browser_app:app --host 127.0.0.1 --port 8000`.
This creates disposable test accounts and token artifacts in `/tmp`, not Git.
Never run that fixture against a production database or expose it publicly.

### Opt-in live smoke tests

Ordinary CI never submits hardware jobs. To explicitly opt into paid smoke tests,
configure the real provider variables above, enable hardware, and set:

```bash
RUN_HARDWARE_INTEGRATION_TESTS=true
HARDWARE_TEST_IBM_DEVICE=<discovered-backend-name>
HARDWARE_TEST_BRAKET_DEVICE=<discovered-QPU-ARN>
HARDWARE_TEST_SHOTS=16
```

Then run `backend/.venv/bin/python -m pytest backend/tests/test_hardware_live.py -q -s`.
Export the variables in the shell; placeholders are not literal configuration.
Each configured provider gets one two-qubit Bell job, at most 32 shots. The test
prints only provider/job identifiers, polls for at most five minutes, checks total
counts and loose statistical plausibility, and does not retry submission. A
queue may exceed the test deadline; retain the printed job ID and inspect it at
the provider rather than rerunning blindly. Devices with higher minimum shots
fail validation and require a separately reviewed manual test. No exact noisy
counts are asserted.

## Known limitations and next step

Live credentials and QPU results remain unverified. IBM dynamic support depends
on actual target/firmware, and Braket intentionally implements a conservative
static gate-model subset. Provider-side physical routing previews, calibration
snapshots, error mitigation, symbolic sweeps, batch jobs, background reconciliation,
webhooks, job pagination beyond the latest 20, automated orphan recovery and
account billing estimates are not implemented. Provider POST acceptance latency
and SDK network retries still depend on the SDK; completion is never awaited in
submission. Queue metadata may be unavailable. Provider clients are process-cached.

The recommended next step is a supervised tiny live acceptance run on each
configured account, followed by an operator recovery/reconciliation worker and
broader device-specific conformance fixtures. Add providers only behind the same
contract, preserving the explicit distinction between simulated internal states
and measured hardware results.

## Changed files and commits

Implementation files: `backend/app/services/hardware/{base,ibm,braket,registry,__init__}.py`,
`backend/app/api/hardware.py`, `backend/app/schemas/{circuit,hardware}.py`,
`backend/app/models/hardware.py`, `backend/app/models/__init__.py`,
`backend/app/core/config.py`, `backend/app/main.py`, `backend/app/migrate.py`,
`backend/migrations/env.py`, `backend/migrations/versions/0002_hardware_jobs.py`,
`backend/requirements*.txt`, `backend/Dockerfile`, `docker-compose.yml`,
`frontend/src/components/circuit-builder/{CircuitBuilder,HardwareExecution}.tsx`,
`frontend/src/lib/api.ts`.

Tests: `backend/tests/{test_hardware,test_hardware_live,hardware_browser_app}.py`,
`backend/tests/test_production.py` (CORS header assertion),
`frontend/tests/browser/simulator-v2-phase4.cjs`.
Documentation/configuration: `.env.example`, `README.md`, this report.

Final browser verification passed all four simulator suites against the production
build after execution-mode enforcement. The hardware boundary remained a fixture.
The disabled-mode check also passed against the ordinary API. All protected branch
references matched their starting hashes, and a credential-pattern scan of current
tracked/new files found no remaining matches. No real hardware run was attempted.

Commit identifiers are recorded below; the documentation commit is the commit
containing this report (inspect with `git log -1 -- docs/SIMULATOR_V2_PHASE4_REPORT.md`).

- `8120fa7` — `feat(hardware): add IBM and Braket adapters with durable authenticated QPU jobs`
- `0fcc34a` — `feat(builder): add explicit QPU confirmation, job monitoring and hardware comparison`
- Documentation/configuration delivery — `docs(hardware): document Phase 4 verification and secure operator configuration`

The implementation and UI commits include their corresponding tests. The report
commit records the final verification results and removes the pre-existing
credential-shaped example value. At delivery, all requested work is committed on
the Phase 4 branch and the working tree is clean; live acceptance remains the
explicit unverified boundary described above.
