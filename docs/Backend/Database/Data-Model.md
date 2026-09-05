# Intelligent Quantum Learning & Research System

## Database Data Model — Revised Version

**Database:** PostgreSQL  
**ORM:** SQLAlchemy  
**Purpose:** Database model for the AI-powered interactive quantum-computing learning and research platform.

### Core workflow

> **Learn → Build → Code → Simulate → Visualize → AI Guidance → Assess → Track Progress**

This model is based on the project requirements, architecture, roadmap, MVP scope, collaboration requirements, gamification requirements, and the previous data-model decisions.

---

# 1. Design Goals

The database should support:

- Student, instructor, researcher, and administrator accounts
- Courses and structured learning modules
- Module progress and weak-area tracking
- Quizzes, coding challenges, and circuit-building assessments
- Quantum circuit creation and version history
- Visual circuit building using gates
- Quantum-code submissions and execution
- Qiskit, PennyLane, and Cirq simulation backends
- Measurement counts, probabilities, state vectors, Bloch data, and circuit diagrams
- AI tutor conversations with circuit/code/simulation context
- AI debugging and optimization context
- Personalized learning recommendations
- Instructor assignments and learner analytics
- XP, levels, streaks, and badges
- Sharing circuits, code, and projects
- Projects with multiple contributors
- Multiple roles for one person, with exactly one primary role and optional secondary roles

---

# 2. Entity Overview

## User & Access

1. `users`
2. `roles`
3. `user_roles`

## Learning

4. `courses`
5. `learning_modules`
6. `module_progress`
7. `learning_recommendations`

## Assessment

8. `assessments`
9. `questions`
10. `question_options`
11. `assessment_attempts`
12. `question_answers`
13. `coding_challenges`
14. `code_submissions`

## Quantum Circuit & Simulation

15. `circuits`
16. `quantum_gates`
17. `circuit_gates`
18. `circuit_versions`
19. `simulation_runs`
20. `simulation_results`

## AI Tutor

21. `ai_conversations`
22. `ai_messages`

## Gamification

23. `user_gamification`
24. `badges`
25. `user_badges`

## Courses & Instructor

26. `course_enrollments`
27. `course_assignments`

## Projects, Contributions & Collaboration

28. `projects`
29. `project_members`
30. `contributions`
31. `contribution_members`
32. `shared_resources`

---

# 3. High-Level ER Structure

```text
                                ┌───────────────┐
                                │    USERS      │
                                └───────┬───────┘
                                        │
                ┌───────────────────────┼────────────────────────┐
                │                       │                        │
                ▼                       ▼                        ▼
        ┌───────────────┐       ┌───────────────┐        ┌────────────────┐
        │ USER_ROLES    │       │   COURSES     │        │   CIRCUITS     │
        └───────┬───────┘       └───────┬───────┘        └───────┬────────┘
                │                       │                        │
                ▼                       ▼                        ├──────────────┐
        ┌───────────────┐       ┌───────────────┐                │              │
        │    ROLES      │       │   MODULES     │                ▼              ▼
        └───────────────┘       └───────┬───────┘        ┌──────────────┐ ┌───────────────┐
                                        │                │CIRCUIT_GATES │ │CIRCUIT_VERSIONS│
                           ┌────────────┼─────────┐      └──────┬───────┘ └───────────────┘
                           ▼            ▼         ▼             │
                    MODULE_PROGRESS ASSESSMENTS CODING_        ▼
                                             CHALLENGES  ┌───────────────┐
                           │            │         │       │ QUANTUM_GATES │
                           │            ▼         ▼       └───────────────┘
                           │       QUESTIONS CODE_SUBMISSIONS
                           │            │
                           │            ▼
                           │      QUESTION_OPTIONS
                           │
                           ▼
                    LEARNING_RECOMMENDATIONS


 USERS ───────< COURSE_ENROLLMENTS >────── COURSES
 USERS ───────< COURSE_ASSIGNMENTS >────── COURSES

 CIRCUITS ────< SIMULATION_RUNS ────────< SIMULATION_RESULTS
 USERS ───────< AI_CONVERSATIONS ────────< AI_MESSAGES
 CIRCUITS ────────┘             │
                                └── context_data

 USERS ───────1 USER_GAMIFICATION
 USERS ───────< USER_BADGES >──────────── BADGES

 USERS ───────< PROJECT_MEMBERS >──────── PROJECTS
 PROJECTS ────< CONTRIBUTIONS
 USERS ───────< CONTRIBUTION_MEMBERS >── CONTRIBUTIONS

 USERS ───────< SHARED_RESOURCES
 PROJECTS ────< SHARED_RESOURCES
 CIRCUITS ────< SHARED_RESOURCES
```

---

# 4. Common PostgreSQL Conventions

### Primary keys

Use UUIDs:

```sql
UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

### Timestamps

Use:

```sql
TIMESTAMP WITH TIME ZONE
```

for application timestamps.

### JSONB

Use `JSONB` where the structure is dynamic, especially:

- Circuit representation
- Gate parameters
- Simulation outputs
- AI context
- Challenge expected output

---

# 5. users

Stores students, instructors, researchers, and administrators.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `user_id` | UUID | PK | Unique user ID |
| `name` | VARCHAR(100) | NOT NULL | User name |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| `password_hash` | TEXT | NULL | Hashed password |
| `avatar_url` | TEXT | NULL | Profile image |
| `created_at` | TIMESTAMPTZ | NOT NULL | Account creation |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update |

> User roles are handled through `roles` and `user_roles` instead of storing only one role in `users`.

This allows one person to have multiple roles.

---

# 6. roles

Master list of available roles.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `role_id` | UUID | PK | Unique role ID |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Role name |
| `description` | TEXT | NULL | Role description |

Recommended roles:

- `student`
- `instructor`
- `researcher`
- `admin`
- `team_lead`
- `frontend_developer`
- `backend_developer`
- `database_developer`
- `ai_developer`
- `quantum_developer`

---

# 7. user_roles

Many-to-many relationship between users and roles.

This implements the agreed rule:

> **One primary role + zero or more secondary roles.**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `user_role_id` | UUID | PK | Unique record |
| `user_id` | UUID | FK → users.user_id | User |
| `role_id` | UUID | FK → roles.role_id | Assigned role |
| `is_primary` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether this is the primary role |
| `assigned_at` | TIMESTAMPTZ | NOT NULL | Assignment time |

### Rules

- A user can have many roles.
- A user must have at most one `is_primary = TRUE` role.
- Secondary roles have `is_primary = FALSE`.
- Unique constraint: `(user_id, role_id)`.

Example:

```text
Tanuj
├── Team Lead       → Primary
└── Database Dev    → Secondary
```

---

# 8. courses

Stores courses created by instructors.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `course_id` | UUID | PK | Unique course |
| `title` | VARCHAR(200) | NOT NULL | Course title |
| `description` | TEXT | NULL | Course description |
| `difficulty` | VARCHAR(30) | NULL | Beginner/Intermediate/Advanced |
| `created_by` | UUID | FK → users.user_id | Instructor |
| `is_published` | BOOLEAN | DEFAULT FALSE | Publication status |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update |

---

# 9. learning_modules

Stores structured learning content inside courses.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `module_id` | UUID | PK | Unique module |
| `course_id` | UUID | FK → courses.course_id | Parent course |
| `title` | VARCHAR(200) | NOT NULL | Module title |
| `description` | TEXT | NULL | Module description |
| `content` | TEXT | NOT NULL | Learning content |
| `module_order` | INTEGER | NOT NULL | Position |
| `difficulty` | VARCHAR(30) | NULL | Difficulty |
| `estimated_minutes` | INTEGER | NULL | Estimated completion time |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update |

Recommended initial modules:

1. Classical vs Quantum Computing
2. Qubits, Superposition & Measurement
3. Quantum Gates
4. Entanglement & Bell States
5. Deutsch-Jozsa Algorithm
6. Grover's Search
7. Quantum Teleportation
8. Shor's Algorithm Overview

---

# 10. module_progress

Tracks learner progress through modules.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `progress_id` | UUID | PK | Unique progress record |
| `user_id` | UUID | FK → users.user_id | Learner |
| `module_id` | UUID | FK → learning_modules.module_id | Module |
| `status` | VARCHAR(30) | NOT NULL | not_started/in_progress/completed |
| `completion_pct` | NUMERIC(5,2) | DEFAULT 0 | Completion percentage |
| `started_at` | TIMESTAMPTZ | NULL | Start time |
| `completed_at` | TIMESTAMPTZ | NULL | Completion time |
| `last_accessed_at` | TIMESTAMPTZ | NULL | Last activity |

**Unique:** `(user_id, module_id)`

---

# 11. learning_recommendations

Stores personalized learning recommendations.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `recommendation_id` | UUID | PK | Unique recommendation |
| `user_id` | UUID | FK → users.user_id | Learner |
| `module_id` | UUID | FK → learning_modules.module_id | Recommended module |
| `reason` | TEXT | NOT NULL | Why it was recommended |
| `priority` | INTEGER | NULL | Recommendation priority |
| `status` | VARCHAR(30) | NOT NULL | pending/completed/dismissed |
| `created_at` | TIMESTAMPTZ | NOT NULL | Created time |
| `completed_at` | TIMESTAMPTZ | NULL | Completion time |

Example:

```text
Weak area: Entanglement
        ↓
Recommend:
- Review Entanglement module
- Try Bell State tutorial
- Complete practice questions
```

---

# 12. assessments

Parent table for quizzes and practical assessments.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `assessment_id` | UUID | PK | Unique assessment |
| `module_id` | UUID | FK → learning_modules.module_id | Related module |
| `title` | VARCHAR(200) | NOT NULL | Assessment title |
| `description` | TEXT | NULL | Description |
| `assessment_type` | VARCHAR(30) | NOT NULL | quiz/coding_challenge/circuit_challenge |
| `max_score` | NUMERIC(6,2) | NOT NULL | Maximum score |
| `passing_score` | NUMERIC(6,2) | NULL | Passing score |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |

---

# 13. questions

Stores questions belonging to assessments.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `question_id` | UUID | PK | Unique question |
| `assessment_id` | UUID | FK → assessments.assessment_id | Assessment |
| `question_text` | TEXT | NOT NULL | Question |
| `question_type` | VARCHAR(30) | NOT NULL | mcq/true_false/short_answer |
| `points` | NUMERIC(6,2) | NOT NULL | Question points |
| `question_order` | INTEGER | NOT NULL | Question position |

---

# 14. question_options

Stores answer choices for multiple-choice questions.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `option_id` | UUID | PK | Unique option |
| `question_id` | UUID | FK → questions.question_id | Question |
| `option_text` | TEXT | NOT NULL | Choice |
| `is_correct` | BOOLEAN | NOT NULL | Correct-answer flag |

---

# 15. assessment_attempts

Stores every learner's attempt.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `attempt_id` | UUID | PK | Unique attempt |
| `assessment_id` | UUID | FK → assessments.assessment_id | Assessment |
| `user_id` | UUID | FK → users.user_id | Learner |
| `score` | NUMERIC(6,2) | NULL | Score |
| `max_score` | NUMERIC(6,2) | NOT NULL | Maximum score |
| `percentage` | NUMERIC(5,2) | NULL | Percentage |
| `status` | VARCHAR(30) | NOT NULL | in_progress/submitted |
| `started_at` | TIMESTAMPTZ | NOT NULL | Start time |
| `submitted_at` | TIMESTAMPTZ | NULL | Submission time |

---

# 16. question_answers

Stores answers to individual questions.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `answer_id` | UUID | PK | Unique answer |
| `attempt_id` | UUID | FK → assessment_attempts.attempt_id | Attempt |
| `question_id` | UUID | FK → questions.question_id | Question |
| `selected_option_id` | UUID | FK → question_options.option_id, NULL | Selected choice |
| `answer_text` | TEXT | NULL | Text answer |
| `is_correct` | BOOLEAN | NULL | Correctness |
| `points_earned` | NUMERIC(6,2) | NULL | Earned points |

---

# 17. coding_challenges

Stores programming-based quantum challenges.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `challenge_id` | UUID | PK | Unique challenge |
| `module_id` | UUID | FK → learning_modules.module_id | Related module |
| `title` | VARCHAR(200) | NOT NULL | Challenge title |
| `description` | TEXT | NULL | Description |
| `instructions` | TEXT | NOT NULL | Instructions |
| `framework` | VARCHAR(30) | NOT NULL | qiskit/pennylane/cirq |
| `starter_code` | TEXT | NULL | Starter code |
| `expected_output` | JSONB | NULL | Expected result |
| `test_code` | TEXT | NULL | Validation tests |
| `difficulty` | VARCHAR(30) | NULL | Difficulty |
| `max_score` | NUMERIC(6,2) | NOT NULL | Maximum score |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |

---

# 18. code_submissions

Stores learner quantum-code submissions.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `submission_id` | UUID | PK | Unique submission |
| `challenge_id` | UUID | FK → coding_challenges.challenge_id | Challenge |
| `user_id` | UUID | FK → users.user_id | Learner |
| `code` | TEXT | NOT NULL | Submitted code |
| `framework` | VARCHAR(30) | NOT NULL | Qiskit/PennyLane/Cirq |
| `execution_output` | TEXT | NULL | Output |
| `error_message` | TEXT | NULL | Execution error |
| `score` | NUMERIC(6,2) | NULL | Score |
| `passed` | BOOLEAN | NULL | Whether tests passed |
| `execution_time_ms` | INTEGER | NULL | Execution time |
| `submitted_at` | TIMESTAMPTZ | NOT NULL | Submission time |

---

# 19. circuits

Stores quantum circuits created by users.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `circuit_id` | UUID | PK | Unique circuit |
| `user_id` | UUID | FK → users.user_id | Owner |
| `name` | VARCHAR(200) | NOT NULL | Circuit name |
| `description` | TEXT | NULL | Description |
| `num_qubits` | INTEGER | NOT NULL | Number of qubits |
| `num_classical_bits` | INTEGER | DEFAULT 0 | Classical bits |
| `source_type` | VARCHAR(20) | NOT NULL | visual/code |
| `framework` | VARCHAR(30) | NULL | Qiskit/PennyLane/Cirq |
| `circuit_data` | JSONB | NOT NULL | Circuit representation |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update |

### Example `circuit_data`

```json
{
  "num_qubits": 2,
  "gates": [
    {
      "gate": "H",
      "qubit": 0,
      "position": 0
    },
    {
      "gate": "CNOT",
      "control": 0,
      "target": 1,
      "position": 1
    }
  ]
}
```

---

# 20. quantum_gates

Master catalog of supported quantum gates.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `gate_id` | UUID | PK | Unique gate |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Gate name |
| `symbol` | VARCHAR(20) | NOT NULL | Display symbol |
| `description` | TEXT | NULL | Gate explanation |
| `num_qubits` | INTEGER | NOT NULL | Number of affected qubits |
| `matrix` | JSONB | NULL | Gate matrix |

Initial gates:

- H
- X
- Y
- Z
- CNOT
- Toffoli
- SWAP
- Measurement

---

# 21. circuit_gates

Stores actual gates placed inside circuits.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `circuit_gate_id` | UUID | PK | Unique placement |
| `circuit_id` | UUID | FK → circuits.circuit_id | Circuit |
| `gate_id` | UUID | FK → quantum_gates.gate_id | Gate |
| `qubit_position` | INTEGER | NOT NULL | Main qubit |
| `control_qubit` | INTEGER | NULL | Control qubit |
| `target_qubit` | INTEGER | NULL | Target qubit |
| `gate_order` | INTEGER | NOT NULL | Order in circuit |
| `parameters` | JSONB | NULL | Gate parameters |

Example:

```text
Q0 ── H ──●── M
          │
Q1 ───────X── M
```

---

# 22. circuit_versions

Maintains circuit/code history.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `version_id` | UUID | PK | Version ID |
| `circuit_id` | UUID | FK → circuits.circuit_id | Circuit |
| `version_number` | INTEGER | NOT NULL | Version number |
| `source_type` | VARCHAR(20) | NOT NULL | visual/code |
| `code` | TEXT | NULL | Code snapshot |
| `circuit_data` | JSONB | NULL | Circuit snapshot |
| `created_by` | UUID | FK → users.user_id | User |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |

**Unique:** `(circuit_id, version_number)`

---

# 23. simulation_runs

Stores executions of quantum circuits.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `simulation_id` | UUID | PK | Simulation ID |
| `circuit_id` | UUID | FK → circuits.circuit_id | Circuit |
| `user_id` | UUID | FK → users.user_id | User |
| `backend` | VARCHAR(50) | NOT NULL | Simulator backend |
| `shots` | INTEGER | NULL | Number of shots |
| `status` | VARCHAR(30) | NOT NULL | queued/running/completed/failed |
| `execution_time_ms` | INTEGER | NULL | Execution time |
| `started_at` | TIMESTAMPTZ | NOT NULL | Start time |
| `completed_at` | TIMESTAMPTZ | NULL | Completion |
| `error_message` | TEXT | NULL | Error |

Supported backends:

- `qiskit_aer`
- `pennylane_default_qubit`
- `cirq_simulator`

The architecture is modular so additional quantum backends can be added later.

---

# 24. simulation_results

Stores simulation outputs.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `result_id` | UUID | PK | Result ID |
| `simulation_id` | UUID | FK → simulation_runs.simulation_id | Simulation |
| `measurement_counts` | JSONB | NULL | Measurement counts |
| `probabilities` | JSONB | NULL | State probabilities |
| `state_vector` | JSONB | NULL | State vector |
| `bloch_data` | JSONB | NULL | Bloch-sphere data |
| `circuit_diagram` | TEXT | NULL | Rendered diagram |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |

Example:

```json
{
  "00": 498,
  "11": 502
}
```

---

# 25. ai_conversations

Stores AI Tutor conversations.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `conversation_id` | UUID | PK | Conversation ID |
| `user_id` | UUID | FK → users.user_id | User |
| `circuit_id` | UUID | FK → circuits.circuit_id, NULL | Related circuit |
| `title` | VARCHAR(200) | NULL | Conversation title |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update |

---

# 26. ai_messages

Stores individual user, assistant, and system messages.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `message_id` | UUID | PK | Message ID |
| `conversation_id` | UUID | FK → ai_conversations.conversation_id | Conversation |
| `sender_type` | VARCHAR(20) | NOT NULL | user/assistant/system |
| `message` | TEXT | NOT NULL | Message content |
| `context_data` | JSONB | NULL | AI context |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |

### `context_data` may contain

```json
{
  "circuit_id": "uuid",
  "simulation_id": "uuid",
  "module_id": "uuid",
  "code": "...",
  "error": "...",
  "simulation_result": {}
}
```

This supports the project's context-aware AI Tutor:

```text
User Question
      +
Current Circuit
      +
Quantum Code
      +
Simulation Result
      +
Learning Module
      +
Learning Progress
      ↓
   AI Tutor
```

---

# 27. user_gamification

Stores learner gamification statistics.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `user_id` | UUID | PK, FK → users.user_id | User |
| `xp` | INTEGER | DEFAULT 0 | Experience points |
| `level` | INTEGER | DEFAULT 1 | Current level |
| `current_streak` | INTEGER | DEFAULT 0 | Current streak |
| `longest_streak` | INTEGER | DEFAULT 0 | Longest streak |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update |

---

# 28. badges

Master list of achievements.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `badge_id` | UUID | PK | Badge ID |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Badge name |
| `description` | TEXT | NOT NULL | Badge description |
| `icon_url` | TEXT | NULL | Badge icon |
| `requirement_type` | VARCHAR(50) | NOT NULL | Requirement type |
| `requirement_value` | INTEGER | NULL | Requirement value |

---

# 29. user_badges

Many-to-many relationship between users and badges.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `user_badge_id` | UUID | PK | Record ID |
| `user_id` | UUID | FK → users.user_id | User |
| `badge_id` | UUID | FK → badges.badge_id | Badge |
| `earned_at` | TIMESTAMPTZ | NOT NULL | Earned time |

**Unique:** `(user_id, badge_id)`

---

# 30. course_enrollments

Tracks students enrolled in courses.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `enrollment_id` | UUID | PK | Enrollment ID |
| `course_id` | UUID | FK → courses.course_id | Course |
| `user_id` | UUID | FK → users.user_id | Learner |
| `status` | VARCHAR(30) | NOT NULL | Enrollment status |
| `enrolled_at` | TIMESTAMPTZ | NOT NULL | Enrollment time |

**Unique:** `(course_id, user_id)`

---

# 31. course_assignments

Allows instructors to assign modules or assessments.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `assignment_id` | UUID | PK | Assignment ID |
| `course_id` | UUID | FK → courses.course_id | Course |
| `module_id` | UUID | FK → learning_modules.module_id, NULL | Assigned module |
| `assessment_id` | UUID | FK → assessments.assessment_id, NULL | Assigned assessment |
| `assigned_by` | UUID | FK → users.user_id | Instructor |
| `due_date` | TIMESTAMPTZ | NULL | Due date |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |

At least one of `module_id` or `assessment_id` should be provided.

---

# 32. projects

Stores collaborative quantum projects.

A project can contain circuits, code, and other shared resources.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `project_id` | UUID | PK | Project ID |
| `owner_id` | UUID | FK → users.user_id | Project owner |
| `name` | VARCHAR(200) | NOT NULL | Project name |
| `description` | TEXT | NULL | Project description |
| `visibility` | VARCHAR(20) | NOT NULL | private/link/public |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update |

---

# 33. project_members

Connects multiple users to a project.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `project_member_id` | UUID | PK | Membership ID |
| `project_id` | UUID | FK → projects.project_id | Project |
| `user_id` | UUID | FK → users.user_id | Contributor |
| `joined_at` | TIMESTAMPTZ | NOT NULL | Join time |

**Unique:** `(project_id, user_id)`

---

# 34. contributions

Represents one logical contribution to a project.

This table is important because **one contribution can be made by multiple people**.

Examples:

- Built Bell State circuit
- Implemented simulation API
- Added AI circuit explanation
- Wrote Grover's Search module

| Column | Type | Constraints | Description |
|---|---|---|---|
| `contribution_id` | UUID | PK | Contribution ID |
| `project_id` | UUID | FK → projects.project_id | Project |
| `title` | VARCHAR(200) | NOT NULL | Contribution title |
| `description` | TEXT | NULL | What was contributed |
| `contribution_type` | VARCHAR(50) | NOT NULL | code/circuit/content/research/documentation |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |

---

# 35. contribution_members

Connects one contribution to one or more users.

This solves the earlier issue:

> **What if the same contribution is done by multiple people?**

Do **not** store only one `user_id` inside `contributions`.

Instead:

```text
CONTRIBUTIONS
      │
      ▼
CONTRIBUTION_MEMBERS
      │
      ├── User A
      ├── User B
      └── User C
```

| Column | Type | Constraints | Description |
|---|---|---|---|
| `contribution_member_id` | UUID | PK | Record ID |
| `contribution_id` | UUID | FK → contributions.contribution_id | Contribution |
| `user_id` | UUID | FK → users.user_id | Contributor |
| `role_in_contribution` | VARCHAR(100) | NULL | What this person did |
| `created_at` | TIMESTAMPTZ | NOT NULL | Record creation |

**Unique:** `(contribution_id, user_id)`

Example:

```text
Contribution:
"Implement Bell State Circuit"

Members:
- User A → Circuit design
- User B → Simulation
- User C → Visualization
```

---

# 36. shared_resources

Supports sharing circuits, code, and projects.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `share_id` | UUID | PK | Share ID |
| `user_id` | UUID | FK → users.user_id | Creator |
| `project_id` | UUID | FK → projects.project_id, NULL | Project |
| `circuit_id` | UUID | FK → circuits.circuit_id, NULL | Circuit |
| `resource_type` | VARCHAR(30) | NOT NULL | circuit/code/project |
| `title` | VARCHAR(200) | NOT NULL | Resource title |
| `description` | TEXT | NULL | Description |
| `share_token` | VARCHAR(100) | UNIQUE, NOT NULL | Share link token |
| `visibility` | VARCHAR(20) | NOT NULL | private/link/public |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation time |
| `expires_at` | TIMESTAMPTZ | NULL | Optional expiration |

---

# 37. Main Relationships

| Parent | Relationship | Child |
|---|---|---|
| `users` | 1:N | `user_roles` |
| `roles` | 1:N | `user_roles` |
| `users` | 1:N | `courses` |
| `courses` | 1:N | `learning_modules` |
| `users` | 1:N | `module_progress` |
| `learning_modules` | 1:N | `module_progress` |
| `learning_modules` | 1:N | `assessments` |
| `assessments` | 1:N | `questions` |
| `questions` | 1:N | `question_options` |
| `assessments` | 1:N | `assessment_attempts` |
| `users` | 1:N | `assessment_attempts` |
| `assessment_attempts` | 1:N | `question_answers` |
| `learning_modules` | 1:N | `coding_challenges` |
| `coding_challenges` | 1:N | `code_submissions` |
| `users` | 1:N | `code_submissions` |
| `users` | 1:N | `circuits` |
| `circuits` | 1:N | `circuit_gates` |
| `quantum_gates` | 1:N | `circuit_gates` |
| `circuits` | 1:N | `circuit_versions` |
| `circuits` | 1:N | `simulation_runs` |
| `simulation_runs` | 1:1 | `simulation_results` |
| `users` | 1:N | `ai_conversations` |
| `ai_conversations` | 1:N | `ai_messages` |
| `users` | 1:N | `learning_recommendations` |
| `learning_modules` | 1:N | `learning_recommendations` |
| `users` | 1:1 | `user_gamification` |
| `users` | N:M | `badges` through `user_badges` |
| `users` | N:M | `courses` through `course_enrollments` |
| `courses` | 1:N | `course_assignments` |
| `users` | 1:N | `projects` |
| `projects` | N:M | `users` through `project_members` |
| `projects` | 1:N | `contributions` |
| `contributions` | N:M | `users` through `contribution_members` |
| `users` | 1:N | `shared_resources` |
| `projects` | 1:N | `shared_resources` |
| `circuits` | 1:N | `shared_resources` |

---

# 38. Important Business Rules

## User roles

A user may have:

```text
1 Primary Role
+
0..N Secondary Roles
```

Example:

```text
User
├── Team Lead       [PRIMARY]
├── Database Dev    [SECONDARY]
└── Backend Dev     [SECONDARY]
```

There must be **at most one primary role per user**.

---

## Contributions

A contribution may have:

```text
1 Contribution
+
1..N Contributors
```

Therefore:

```text
contributions
      ↓
contribution_members
      ↓
multiple users
```

This correctly supports shared work.

---

## Circuit ownership

A circuit has one owner through `circuits.user_id`.

A circuit may also be included in a collaborative project through project/shared-resource relationships.

---

## Assessment attempts

One user can attempt an assessment multiple times.

```text
User
  ↓
Assessment Attempts
  ↓
Question Answers
```

---

## Simulation

A circuit can be simulated many times.

```text
Circuit
   ↓
Simulation Run
   ↓
Simulation Result
```

This preserves simulation history.

---

## AI context

AI messages can optionally reference:

- Current circuit
- Simulation
- Code
- Error
- Learning module
- Other contextual information

Dynamic context is stored in `ai_messages.context_data`.

---

# 39. MVP Database

For the hackathon MVP, implement these first:

### Authentication & Users

- `users`
- `roles`
- `user_roles`

### Learning

- `courses`
- `learning_modules`
- `module_progress`

### Assessment

- `assessments`
- `questions`
- `question_options`
- `assessment_attempts`
- `question_answers`

### Quantum

- `circuits`
- `quantum_gates`
- `circuit_gates`
- `simulation_runs`
- `simulation_results`

### AI

- `ai_conversations`
- `ai_messages`

### Coding

- `coding_challenges`
- `code_submissions`

Then add:

- `user_gamification`
- `badges`
- `user_badges`
- `course_enrollments`
- `course_assignments`
- `learning_recommendations`
- `circuit_versions`
- `projects`
- `project_members`
- `contributions`
- `contribution_members`
- `shared_resources`

---

# 40. Recommended Indexes

Create indexes on:

```text
users.email

user_roles.user_id
user_roles.role_id

learning_modules.course_id

module_progress.user_id
module_progress.module_id

assessments.module_id

questions.assessment_id

assessment_attempts.user_id
assessment_attempts.assessment_id

question_answers.attempt_id

coding_challenges.module_id
code_submissions.user_id
code_submissions.challenge_id

circuits.user_id
circuit_gates.circuit_id
circuit_versions.circuit_id

simulation_runs.circuit_id
simulation_runs.user_id

ai_conversations.user_id
ai_conversations.circuit_id
ai_messages.conversation_id

learning_recommendations.user_id
learning_recommendations.module_id

course_enrollments.user_id
course_enrollments.course_id

course_assignments.course_id

projects.owner_id
project_members.project_id
project_members.user_id

contributions.project_id
contribution_members.contribution_id
contribution_members.user_id

shared_resources.share_token
shared_resources.project_id
shared_resources.circuit_id
```

---

# 41. Backend Integration

The model supports the planned FastAPI API:

| API | Main Tables |
|---|---|
| `POST /api/auth/register` | `users`, `roles`, `user_roles` |
| `POST /api/auth/login` | `users`, `user_roles` |
| `POST /api/circuits/simulate` | `circuits`, `simulation_runs`, `simulation_results` |
| `POST /api/code/execute` | `code_submissions` |
| `POST /api/ai/chat` | `ai_conversations`, `ai_messages` |
| `POST /api/ai/debug` | `ai_messages`, circuit/simulation context |
| `GET /api/progress/{user_id}` | `module_progress`, `assessment_attempts`, `code_submissions` |
| `POST /api/progress/{user_id}/update` | `module_progress` |
| `POST /api/collaborate/share` | `shared_resources` |
| `GET /api/collaborate/{share_id}` | `shared_resources` |

---

# 42. Complete Data Flow

```text
                         USER
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          LEARN         BUILD         CODE
             │            │            │
             ▼            ▼            ▼
        MODULES        CIRCUITS    SUBMISSIONS
             │            │            │
             │            ▼            │
             │       SIMULATION        │
             │            │            │
             │            ▼            │
             │       SIMULATION        │
             │        RESULTS          │
             │            │            │
             └────────────┼────────────┘
                          ▼
                    AI TUTOR
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          EXPLAIN       DEBUG       OPTIMIZE
                          │
                          ▼
                    ASSESSMENTS
                          │
                          ▼
                    PROGRESS
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
       RECOMMENDATIONS     XP        BADGES
                          │
                          ▼
                    DASHBOARDS

                    COLLABORATION
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
          PROJECTS              SHARED RESOURCES
              │
              ▼
        CONTRIBUTIONS
              │
              ▼
      MULTIPLE CONTRIBUTORS
```

---

# 43. Why This Version Is Better

Compared with the earlier 26-table model, this version keeps the original learning, assessment, quantum, AI, simulation, dashboard, gamification, instructor, and sharing functionality while explicitly handling two important project requirements:

### Multiple roles

Instead of:

```text
users.role
```

the model uses:

```text
users
  ↓
user_roles
  ↓
roles
```

This supports one primary role and multiple secondary roles.

### Shared contributions

Instead of forcing one person onto a contribution:

```text
contributions.user_id
```

the model uses:

```text
contributions
       ↓
contribution_members
       ↓
User A
User B
User C
```

This supports a contribution completed by multiple people without duplicating the contribution itself.

### Collaboration

Projects and project membership are separated from individual contributions:

```text
PROJECT
   │
   ├── PROJECT_MEMBERS
   │
   └── CONTRIBUTIONS
          │
          └── CONTRIBUTION_MEMBERS
```

This makes the model suitable for the team's collaborative workflow while remaining compatible with the hackathon MVP.

---

# 44. Final Table Count

| Area | Tables |
|---|---:|
| User & Access | 3 |
| Learning | 4 |
| Assessment | 7 |
| Quantum Circuit & Simulation | 6 |
| AI | 2 |
| Gamification | 3 |
| Course & Instructor | 2 |
| Projects & Collaboration | 5 |
| **Total** | **32** |

> **Recommended implementation strategy:** build the MVP subset first, then add the collaboration, personalization, gamification, and advanced-history tables after the core Learn → Build → Code → Simulate → Visualize → AI → Assess flow is working.
