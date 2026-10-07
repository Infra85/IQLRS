# Curriculum scientific review — Phase 1

## Executive summary

All eight introductions, objectives, 24 sections and diagrams, eight worked examples, takeaway sets and 24 questions (including every option and explanation) were reviewed and revised. The previous content conflated superposition with readable parallel computation, suggested instantaneous entanglement signalling, included two correct answers in a Bell-state question, overstated Deutsch–Jozsa, misstated its worked result, chose an inferior Grover iteration count, hid teleportation bit conventions and overstated QFT’s role in factoring.

The revision teaches ideal pure-state examples with explicit assumptions, distinguishes amplitudes from probabilities and explains where theory exceeds current product capabilities. New descriptors prepare later interactive work without implementing its runtime. Simulator V2 and hardware contracts are unchanged.

Source verification used IBM Quantum Learning and original Grover, teleportation and Shor publications, checked on 2026-10-08. Calculations were independently checked with the existing IQLRS statevector engine. Automated schema checks establish structure; semantic uniqueness of quiz answers is an editorial review responsibility, not something a valid answer index proves.

## Scientific review table

| Module | Topic | Previous issue | Correction | Scientific rationale |
|---|---|---|---|---|
| 1 | Qubit | “0 and 1 simultaneously” and quantum parallelism | Normalized complex amplitudes in a specified basis | Superposition is a coherent linear combination, not two readable classical values |
| 1 | Scope | A state vector implicitly described every state | Explicit pure-state scope | Mixed states generally require density operators |
| 1 | Phase | Phase distinctions omitted | Global phase versus observable relative phase | A common phase leaves all outcome probabilities unchanged |
| 1 | Bloch sphere | A quiz conflated sphere coordinates and amplitudes | Surface representation of pure single-qubit states, with angular formula | Bloch coordinates are real expectation values, not complex vector entries |
| 1 | Measurement | “Forces” and destroys superposition without qualification | Born probabilities and conditional state update; repeat a basis measurement | Measurement of an eigenstate need not change it |
| 1 | Quiz/example | Notation memorization and answer repetition | Complex-amplitude probability, normalization, repeat measurement | Learners calculate and predict rather than recognize typography |
| 2 | Tensor products | Every n-qubit state written as a product | Tensor product of spaces; only product states factor | Entangled pure vectors belong to the joint space without factoring |
| 2 | Worked example | Entangled example stood in for generic superposition | Expand H on both qubits; contrast Bell support | Four equal product amplitudes differ from two correlated Bell amplitudes |
| 2 | Capacity | “Process multiple states at once” | Dimension versus one n-bit outcome per preparation | Exponential state description is not freely accessible classical memory |
| 2 | Interference | H described only as creating randomness | H twice returns the input | Cancellation distinguishes coherent evolution from probabilistic mixing |
| 2 | Quiz | Unnormalized “Bell” answer | Normalized product-state discrimination and probability calculation | Vectors must normalize; superposition does not imply entanglement |
| 3 | Basis | Asked to infer the original state from one X outcome | Given preparation; ask X-basis probabilities | One outcome generally cannot identify preparation |
| 3 | Basis rotation | Measurement implementation unstated | H before Z gives X statistics; H afterward restores X eigenstate representation | Rotated readout statistics and physical post-measurement wire state differ |
| 3 | Entanglement | “Instantaneously fixes” the partner | Conditional joint description; unchanged local unconditioned statistics | No-signalling forbids controllable remote communication |
| 3 | Information | Measurement implied total destruction | Eigenstate example and limited inference from a shot | Local projective measurement is not universal erasure of information |
| 4 | Definition | Pure-state scope easy to overlook | Nonfactorization explicitly restricted to pure bipartite states | Mixed-state separability has a different criterion |
| 4 | Correlations | Stronger than any classical correlation unqualified | Suitable Bell-test settings and local hidden-variable assumptions | Matching Z outcomes alone are classically reproducible |
| 4 | Bell readout | Said two states distinguishable, then vague probabilistic identification | Φ/Ψ families identifiable, signs invisible in Z; explicit joint decoder | Relative signs vanish in squared magnitudes in this basis |
| 4 | Quiz | Both Ψ+ and Φ+ were correct answers | Ask specifically for Φ+ | Exactly one normalized option now answers the question |
| 4 | Circuit | Bit convention unstated | Intermediate state after H(q0) is (00+01)/√2 in q1q0 order | q0 is least significant in IQLRS |
| 5 | Problem | Total-function claim | Constant-or-balanced promise, out-of-promise counterexample | Guarantee is defined only on promised inputs |
| 5 | Classical cost | 2^n worst-case queries | 2^(n−1)+1 exact deterministic queries with adversary reasoning | Half identical answers remain compatible with both cases |
| 5 | Quantum cost | One query implied universal runtime advantage | One oracle use; synthesis/gates/readout excluded; randomized caveat | Bounded-error random sampling needs no exponential number of queries |
| 5 | Oracle | “Controlled-f” hid target action | Reversible XOR oracle and target in minus state | X eigenvalue −1 creates phase kickback |
| 5 | Readout | One input qubit optionally sufficient | Measure every input qubit, test all-zero string | Balance can produce a nonzero bit elsewhere |
| 5 | Worked result | Given truth table claimed 11 | f(x1x0)=x0 yields input 01; target excluded | Walsh transform of (1,−1,1,−1) has support at 01 |
| 6 | Oracle | Scalar −1 incorrectly replaced a ket | U_f acting on a ket with a phase factor | Unitary phase marking preserves norm and immediate Z probabilities |
| 6 | Diffusion | Mechanism mostly named, not explained | Reflection 2|s⟩⟨s|−I and amplitude mean | Derives the two-qubit result without a search-parallelism metaphor |
| 6 | Quiz scaling | Nested big-O answer choices can have more than one valid upper bound | Ask proportional growth at the first peak | A tight growth question distinguishes √N from N without treating big-O as equality |
| 6 | Iterations | π√N/4 treated as an exact choice; N=16 answer 4 | First-peak integer check using sin²((2k+1)θ); answer 3 | k=3 yields 0.96132 versus k=4 at 0.58170 |
| 6 | Marked count | Unqualified generality and success | Known M changes θ; unknown M needs strategy; noise caveat | Amplification oscillates and does not universally give certainty |
| 7 | Protocol | Resources without wire/bit mapping | q0 input, q1/q2 pair, q0→c0, q1→c1 | Corrections are convention-sensitive |
| 7 | Correction | Displayed 10 required X then Z | In c1c0, 10 requires X; 11 requires X then Z | q1 outcome controls X; q0 outcome controls Z |
| 7 | No-cloning | “Destroyed” and ambiguous quiz alternatives | Sender no longer retains unknown input; bits are correction labels | Teleportation transfers the state, not an additional copy |
| 7 | Causality | Classical communication not tied to local state | Receiver before bits has no local input information | The protocol cannot signal faster than light |
| 8 | Order | Any exponent returning 1 called period | Least positive exponent; gcd precheck and retries | Multiples of the order need not satisfy the useful reduction conditions |
| 8 | QFT | Directly reveals r and supplies exponential speedup | Samples related to s/r; classical continued fractions and checks | QFT is one part of order inference, not a factoring oracle |
| 8 | Complexity | Unqualified exponential statement | Polynomial in log N; superpolynomial over known general classical methods | Best known classical factoring is subexponential in bit length; no universal lower bound is proved |
| 8 | Example/product | Arithmetic could imply an implemented quantum circuit | Explicit classical N=15 reduction and failed a=14 comparison | Small arithmetic verifies the reduction, not scalable modular exponentiation |

## Module-by-module teaching review and intentional simplifications

1. **Qubits & Quantum States:** complex-amplitude calculation, normalization and repeat measurement replace vocabulary recall. X preparation is introduced for the planned challenge. The Bloch sphere is explained as a representation, not another state vector. Density matrices and interpretations of measurement are deferred.
2. **Superposition:** expand a product, contrast entanglement, then reverse a Hadamard layer. Equal-superposition probabilities remain useful. The normalized pure-state scope avoids claiming all mixed states are vectors. No proof of the Holevo bound or tomography scaling is required; only the claim that amplitudes are not freely readable storage.
3. **Measurement:** predict outcomes from a specified state and basis. Distinguish ideal X projection from H followed by physical Z readout. Local statistics and conditional correlations replace instantaneous causal language. General POVMs, density-matrix derivations and readout calibration are intentionally outside scope.
4. **Entanglement:** show why the Bell amplitudes cannot factor, list all four normalized Bell states and distinguish family readout from phase-sensitive decoding. The original double-correct quiz is repaired. CHSH is referenced, not derived; mixed entanglement and distributed Bell discrimination are deferred. Full discrimination assumes joint access to both qubits for CNOT decoding.
5. **Deutsch–Jozsa:** three conceptual checks now cover the promise, query-versus-runtime distinction and the deterministic classical count. Phase kickback and all-input readout are derived. The worked oracle is a hand-built three-wire example, not arbitrary oracle synthesis. Randomized bounded-error classical algorithms are acknowledged; formal query lower-bound proofs remain outside scope.
6. **Grover:** trace marking, mean reflection and a first useful peak. The quiz contrasts query scaling, finite-size iteration choice and phase-only probabilities. One marked item is the main example; the M-dependent formula explains the limitation. Unknown-M search strategies, exact amplitude-amplification variants and resource-efficient large oracles are deferred.
7. **Teleportation:** follow the gates, write the two destinations, then apply the correction table. Quiz items test classical communication, an explicitly labeled branch and transfer without a copy. Tests cover arbitrary complex phase as well as the real-amplitude example. Noise, entanglement distribution and physical communication channels are not implemented by this lesson.
8. **Shor overview:** introduce modular remainder, coprimality and least positive order, then separate quantum sampling from classical inference and gcds. Three questions distinguish the tasks and complexity variable. Continued-fraction implementation, success-bound proofs, modular-exponentiation circuits and fault-tolerant resources remain outside scope. This lesson is explicitly not full Shor execution.

All 24 questions have four distinct options, one editorially defensible answer, a stated preparation/convention where relevant, and a reasoning explanation. The assessment IDs and three-question denominators remain unchanged; rewritten questions are not claimed to be identical historical assessment content.

## Scientific conventions and independent derivations

- Pure computational-basis vectors are normalized; P(x)=|αₓ|². General rank-one orthonormal projective measurement uses P(φᵢ)=|⟨φᵢ|ψ⟩|².
- IQLRS quantum integers use q0 as the least significant bit, displaying `q(n−1)…q0`. In two-qubit tensor notation the left factor is q1. A logical oracle expression `|x,y⟩` labels inputs and target; the worked physical full state is `|q2 q1 q0⟩`, with target q2 on the left. The logical labels do not silently redefine wire ordering.
- The examples explicitly map qj→cj. A single two-bit classical register displays c1c0. Explicitly mapped readouts include the written classical destinations, not every unmeasured wire. Multi-register behavior remains governed by [Simulator V2](SIMULATOR_V2.md); no new ordering is introduced here.
- “Measure” in worked circuits is computational-basis measurement unless a basis rotation is stated. Exact probabilities describe ideal preparations; counts from shots fluctuate. A dynamic simulator state vector describes the final conditional shot, not an ensemble mixture.
- Bell preparation: `00 → (00+01)/√2 → (00+11)/√2`. Joint CNOT(q0,q1), H(q0) decoding yields Φ+→00, Φ−→01, Ψ+→10, Ψ−→11 up to global phase.
- Deutsch–Jozsa: the stated table is x0. Oracle kickback gives input amplitudes `(1,−1,1,−1)/2`. Its two-bit Walsh transform is `(0,1,0,0)`, hence input readout 01. Tests independently sum the truth-table transform, compare simulator marginals and check mapped readout. Constant zero yields 00.
- Grover: after marking 11, amplitudes are `(1/2,1/2,1/2,−1/2)`, mean 1/4; `2ā−aₓ` yields `(0,0,0,1)`. The provided gate implementation differs from D by a global minus sign, which tests preserve rather than silently ignoring. For N=16, θ=arcsin(1/4); k=2,3,4 success probabilities are 0.908447265625, 0.9613189697265625, 0.5817041397094727. These are compared near the first peak, not asserted to be a global optimum over arbitrarily many iterations.
- Teleportation: before correction, Bob has `X^{c1}Z^{c0}|ψ⟩` up to global phase. Applying X first, then Z, inverts this. Tests force each nonzero branch through the engine’s existing RNG injection, verify each has probability 1/4, check actual classical display ordering and compare receiver/input fidelity. Five input preparations include basis states and nontrivial complex phase; all 20 branch/input cases have unit ideal fidelity.
- Shor reduction: powers of 2 modulo 15 are 2,4,8,1, establishing least order 4. Half-power 4 produces gcds 3 and 5. The comparison a=14 has order 2 and half-power −1 mod 15, yielding trivial gcds. This verifies arithmetic only.

## Data flow, compatibility and deployment

The audit found that lesson pages do **not** fetch `LearningModule.content`: they render a checked-in TypeScript bundle. Backend quiz scoring reads `MODULES` from JSON; seeding also stores that lesson JSON as text in the database. There is no existing curriculum API/schema to redesign. The Phase 1 solution preserves these paths and adds a reproducible frontend generator with parity checks.

`modules.json → validated curriculum service → existing seed/migration → LearningModule.content` remains intact. New metadata lives in that JSON. The already-existing `difficulty` and `estimated_minutes` columns are populated for new/recognized bundled rows. No database DDL, Alembic revision or table rebuild is required. `curriculumVersion: 2` is a content version, distinct from database migration versions.

Run the existing `PYTHONPATH=backend backend/.venv/bin/python -m app.migrate` with the deployment's normal DATABASE_URL before accepting traffic, and deploy the matching frontend build. The migration retains its transaction and advisory lock. Missing rows are seeded as before. A guarded content upgrade recognizes only the exact previous bundle using canonical JSON SHA-256 hashes, stable course/author identity and unchanged title/order/metadata/assessment configuration. Customized, malformed, unrecognized or independently authored rows are preserved and a warning identifies the module for manual review. No wholesale reseed is performed. A current row is a no-op on subsequent runs.

The hash manifest contains no historical lesson text. `backend/tests/fixtures/curriculum_v1.json` deliberately archives the old, scientifically incorrect bundle for upgrade tests; it is never imported by production code. Do not “correct” that historical fixture. Unknown customization is never approved for overwrite merely because it uses a bundled UUID.

Stable UUID5 module and assessment identifiers, progress, enrollments, attempts and question/option rows are retained. Bundled quizzes historically use JSON questions rather than Question/QuestionOption rows; custom question rows prevent an automatic content upgrade. Historical attempts store scores and denominators, not a snapshot of the original questions. They remain historical scores and are not regraded or represented as evidence of mastery of the revised wording. The shipped curriculum remains the source for live lesson display and bundled quiz grading even when a customized DB row is intentionally retained.

Rollback of an upgraded installation should use its pre-release backup and matching previous application release; this content upgrade does not automatically downgrade edited rows. The migration is idempotent and transactional, not destructively reversible by deleting activity.

Existing frontend behavior is retained: Modules 1–3 have no example builder button; Module 4 has its existing Bell challenge; Module 6 has its existing Grover challenge; Modules 5,7,8 open the generic builder. Legacy `tryInBuilder`/`builderLink` fields are preserved even though the page’s existing routing chooses these challenge URLs. Planned descriptors are never displayed as raw JSON and do not execute anything.

## References

The per-module `references` arrays identify the relevant subset. The following sources were opened and checked; equations and prose in the curriculum are editorial explanations and independently calculated examples, not copied lesson text.

- [IBM: single-system quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information): amplitudes, normalization, Born rule, phase and basis states (Modules 1–3).
- [IBM: Bloch sphere](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere): pure surface states, mixed interior and phase equivalence (Module 1).
- [IBM: multiple-system quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information): tensor products, joint vectors and entanglement (Modules 2,4).
- [IBM: CHSH game](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/chsh-game): measurement-setting-dependent nonclassical correlations (Module 4).
- [IBM: Deutsch–Jozsa](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/quantum-query-algorithms/deutsch-jozsa-algorithm): promise, query comparison, kickback and all-input readout (Module 5).
- [Grover, 1996](https://arxiv.org/abs/quant-ph/9605043) and [IBM: choosing the number of iterations](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/grover-algorithm/number-of-iterations): query scaling and rotation analysis (Module 6).
- [Bennett et al., 1993](https://doi.org/10.1103/PhysRevLett.70.1895) and [IBM: quantum teleportation](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/quantum-teleportation): protocol, corrections and classical communication (Modules 3,7). IQLRS bit labels were verified against its engine rather than assumed from an external diagram.
- [Shor, 1995/1997](https://arxiv.org/abs/quant-ph/9508027) and [IBM: Shor’s algorithm](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/phase-estimation-and-factoring/shor-algorithm): factoring reduction, Fourier sampling, continued fractions and complexity (Module 8).

## Final editorial QA

Each module now supports the requested learner explanation: amplitudes and normalization (1); dimension versus capacity and product versus entangled states (2); measurement with no-signalling (3); Bell factorization and hidden phase (4); promise and query comparison (5); phase marking, diffusion and finite iteration choice (6); labeled correction bits, no copy and classical communication (7); factoring → order finding → Fourier samples plus classical inference (8).

Repository searches reviewed `exponentially faster`, `simultaneously`, `instantaneously`, `always`, `never`, `exactly`, `certainty`, `2^n`, `collapse`, `parallel`, `teleport`, `speedup`, `multiple backends` and `implemented` in context. Remaining live-lesson hits are qualified predictions, explicit limitations, mathematical definitions or reviewed distractors. Simulator documentation uses collapse operationally for its conditional trajectory semantics and was left unchanged. Historical v1 fixture errors are intentionally retained only for migration testing. Legacy architecture claims are labeled as historical and linked to the current implementation.

## Validation record

Commands below were run from the repository root unless marked `frontend/`. PostgreSQL tests used an isolated local database; browser tests used a synthetic learner in that database. No live hardware jobs or external messages were sent.

| Check | Exact command | Result |
|---|---|---|
| Full backend | `TEST_DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_curriculum_check PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q` | 553 passed, 2 skipped, 0 failed |
| Focused curriculum | `TEST_DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_curriculum_check PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_curriculum.py backend/tests/test_curriculum_science.py -q` | 80 passed, 0 skipped, 0 failed |
| Backend lint, including new tests | `backend/.venv/bin/ruff check backend/app/ backend/tests/test_curriculum.py backend/tests/test_curriculum_science.py` | Passed |
| Frontend tests (`frontend/`) | `npm test` | 36 passed, 0 skipped, 0 failed |
| Frontend types (`frontend/`) | `npm run typecheck` | Passed |
| Frontend lint (`frontend/`) | `npm run lint` | Passed; no ESLint warnings/errors |
| Production build (`frontend/`) | `npm run build` | Passed; 12 static pages generated, dynamic lesson route compiled |
| Generated bundle parity | `node frontend/scripts/sync-curriculum.cjs --check` | Passed, also enforced by frontend tests |
| Browser | `NODE_PATH=/tmp/iqlrs-browser-check/node_modules node /tmp/iqlrs-curriculum-browser.cjs` | 8 lesson renders, 24 question explanations, 8 authenticated API submissions/retries, 5 existing builder links; no page errors |
| Migration replay | `DATABASE_URL=postgresql://shaquib@127.0.0.1:55439/iqlrs_curriculum_release_check PYTHONPATH=backend backend/.venv/bin/python /tmp/iqlrs-release-migration.py` | Existing migration ran twice; eight stored lessons match bundle; second run changed no lesson timestamps |
| Whitespace | `git diff --check` | Passed |

The browser wrapper reads a temporary local token without logging it, then invokes the committed `frontend/tests/browser/curriculum.cjs`. Reproduce with Playwright available, a production frontend at `CURRICULUM_URL` (default localhost:13002), its real API, and `CURRICULUM_TOKEN` belonging to an isolated learner. The migration wrapper invokes `app.migrate.migrate()` twice and checks stored lesson content and timestamps; persistence tests additionally exercise a real v1 upgrade, customized-row preservation and historical activity retention.

The backend emits one existing Starlette/AnyIO deprecation warning. The two skips are IBM and Braket paid smoke tests requiring explicit opt-in. Next emits its existing `next lint` deprecation notice. Early non-database runs skipped integration tests; final configured runs above exercised them. One frontend run hit sandbox `EPERM` on the generator subprocess; the permitted rerun passed. New-test lint formatting issues were corrected. One build invocation from the repository root reported no build script; the actual frontend build was subsequently run successfully from `frontend/`. No tests were disabled or altered to hide failures.
