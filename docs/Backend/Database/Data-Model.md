Intelligent Quantum Learning & Research System

Database Data Model

Database: PostgreSQL
Purpose: Data model for the AI-powered interactive quantum computing learning, simulation, assessment, progress, instructor, and collaboration platform.

The model supports the workflow:

Learn → Build → Code → Simulate → Visualize → AI Guidance → Assess → Track Progress

1. Entity Overview

Core Entities

users

courses

learning_modules

module_progress

Assessment Entities

assessments

questions

question_options

assessment_attempts

question_answers

coding_challenges

code_submissions

Quantum Circuit & Simulation Entities

circuits

quantum_gates

circuit_gates

circuit_versions

simulation_runs

simulation_results

AI Entities

ai_conversations

ai_messages

learning_recommendations

Gamification Entities

user_gamification

badges

user_badges

Instructor & Collaboration Entities

course_enrollments

course_assignments

shared_resources

2. Entity Relationship Diagram

                                      ┌──────────────────┐
                                      │      USERS       │
                                      │──────────────────│
                                      │ PK user_id       │
                                      │ name             │
                                      │ email            │
                                      │ password_hash     │
                                      │ role             │
                                      └────────┬─────────┘
                                               │
              ┌────────────────────────────────┼────────────────────────────────┐
              │                                │                                │
              │                                │                                │
              ▼                                ▼                                ▼
      ┌─────────────────┐              ┌─────────────────┐              ┌──────────────────┐
      │     COURSES     │              │    CIRCUITS     │              │ AI_CONVERSATIONS │
      └────────┬────────┘              └────────┬────────┘              └────────┬─────────┘
               │                               │                                │
               ▼                               ├──────────────┐                 ▼
      ┌─────────────────┐                      │              │          ┌──────────────────┐
      │ LEARNING_MODULES│                      ▼              ▼          │    AI_MESSAGES   │
      └────────┬────────┘              ┌──────────────┐ ┌──────────────┐ └──────────────────┘
               │                       │CIRCUIT_GATES │ │CIRCUIT_      │
               │                       └──────┬───────┘ │VERSIONS       │
               │                              │         └──────────────┘
               ├──────────────┐               ▼
               │              │       ┌────────────────┐
               ▼              ▼       │ QUANTUM_GATES  │
      ┌────────────────┐ ┌──────────────┐└────────────────┘
      │MODULE_PROGRESS │ │ ASSESSMENTS  │
      └────────────────┘ └──────┬───────┘
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
          ┌─────────────┐ ┌───────────┐ ┌──────────────────┐
          │  QUESTIONS  │ │ CODING_   │ │ASSESSMENT_ATTEMPTS│
          └──────┬──────┘ │ CHALLENGES│ └────────┬─────────┘
                 │        └─────┬─────┘          │
                 ▼              ▼                ▼
        ┌────────────────┐ ┌───────────────┐ ┌────────────────┐
        │QUESTION_OPTIONS│ │CODE_SUBMISSIONS│ │QUESTION_ANSWERS│
        └────────────────┘ └───────────────┘ └────────────────┘


 USERS ───────────────< COURSE_ENROLLMENTS >────────────── COURSES
 USERS ───────────────< COURSE_ASSIGNMENTS >────────────── COURSES

 CIRCUITS ────────────< SIMULATION_RUNS ────────────────< SIMULATION_RESULTS

 USERS ───────────────< LEARNING_RECOMMENDATIONS >────── LEARNING_MODULES

 USERS ───────────────1 USER_GAMIFICATION
 USERS ───────────────< USER_BADGES >─────────────────── BADGES

 USERS ───────────────< SHARED_RESOURCES
 CIRCUITS ────────────< SHARED_RESOURCES

3. users

Stores students, instructors, researchers, and administrators.

Column

Type

Constraints

Description

user_id

UUID

PK

Unique user ID

name

VARCHAR(100)

NOT NULL

User's name

email

VARCHAR(255)

UNIQUE, NOT NULL

Login email

password_hash

TEXT

NULL

Hashed password

role

VARCHAR(20)

NOT NULL

student/instructor/researcher/admin

avatar_url

TEXT

NULL

Profile image

created_at

TIMESTAMP

NOT NULL

Account creation time

updated_at

TIMESTAMP

NOT NULL

Last update time

4. courses

Stores courses created by instructors.

Column

Type

Constraints

Description

course_id

UUID

PK

Unique course

title

VARCHAR(200)

NOT NULL

Course title

description

TEXT

NULL

Course description

difficulty

VARCHAR(30)

NULL

Beginner/Intermediate/Advanced

created_by

UUID

FK → users.user_id

Instructor

is_published

BOOLEAN

DEFAULT FALSE

Publication status

created_at

TIMESTAMP

NOT NULL

Creation time

updated_at

TIMESTAMP

NOT NULL

Last update

5. learning_modules

Stores structured learning content.

Column

Type

Constraints

Description

module_id

UUID

PK

Unique module

course_id

UUID

FK → courses.course_id

Parent course

title

VARCHAR(200)

NOT NULL

Module title

description

TEXT

NULL

Module description

content

TEXT

NOT NULL

Learning content

module_order

INTEGER

NOT NULL

Position in course

difficulty

VARCHAR(30)

NULL

Module difficulty

estimated_minutes

INTEGER

NULL

Estimated completion time

created_at

TIMESTAMP

NOT NULL

Creation time

updated_at

TIMESTAMP

NOT NULL

Last update

Example modules:

Classical vs Quantum Computing

Qubits, Superposition & Measurement

Quantum Gates

Entanglement & Bell States

Deutsch-Jozsa Algorithm

Grover's Search

Quantum Teleportation

Shor's Algorithm

6. module_progress

Tracks individual learner progress through modules.

Column

Type

Constraints

progress_id

UUID

PK

user_id

UUID

FK → users.user_id

module_id

UUID

FK → learning_modules.module_id

status

VARCHAR(30)

NOT NULL

completion_pct

NUMERIC(5,2)

DEFAULT 0

started_at

TIMESTAMP

NULL

completed_at

TIMESTAMP

NULL

last_accessed_at

TIMESTAMP

NULL

Recommended status values:

not_started
in_progress
completed

Unique constraint:

(user_id, module_id)

7. assessments

Parent table for quizzes and practical assessments.

Column

Type

Constraints

assessment_id

UUID

PK

module_id

UUID

FK → learning_modules.module_id

title

VARCHAR(200)

NOT NULL

description

TEXT

NULL

assessment_type

VARCHAR(30)

NOT NULL

max_score

NUMERIC(6,2)

NOT NULL

passing_score

NUMERIC(6,2)

NULL

created_at

TIMESTAMP

NOT NULL

Assessment types:

quiz
coding_challenge
circuit_challenge

8. questions

Stores questions belonging to assessments.

Column

Type

Constraints

question_id

UUID

PK

assessment_id

UUID

FK → assessments.assessment_id

question_text

TEXT

NOT NULL

question_type

VARCHAR(30)

NOT NULL

points

NUMERIC(6,2)

NOT NULL

question_order

INTEGER

NOT NULL

Question types can include:

mcq
true_false
short_answer

9. question_options

Stores choices for multiple-choice questions.

Column

Type

Constraints

option_id

UUID

PK

question_id

UUID

FK → questions.question_id

option_text

TEXT

NOT NULL

is_correct

BOOLEAN

NOT NULL

10. assessment_attempts

Stores each student's assessment attempt.

Column

Type

Constraints

attempt_id

UUID

PK

assessment_id

UUID

FK → assessments.assessment_id

user_id

UUID

FK → users.user_id

score

NUMERIC(6,2)

NULL

max_score

NUMERIC(6,2)

NOT NULL

percentage

NUMERIC(5,2)

NULL

status

VARCHAR(30)

NOT NULL

started_at

TIMESTAMP

NOT NULL

submitted_at

TIMESTAMP

NULL

11. question_answers

Stores answers to individual questions.

Column

Type

Constraints

answer_id

UUID

PK

attempt_id

UUID

FK → assessment_attempts.attempt_id

question_id

UUID

FK → questions.question_id

selected_option_id

UUID

FK → question_options.option_id, NULL

answer_text

TEXT

NULL

is_correct

BOOLEAN

NULL

points_earned

NUMERIC(6,2)

NULL

12. coding_challenges

Stores programming-based quantum challenges.

Column

Type

Constraints

challenge_id

UUID

PK

module_id

UUID

FK → learning_modules.module_id

title

VARCHAR(200)

NOT NULL

description

TEXT

NULL

instructions

TEXT

NOT NULL

framework

VARCHAR(30)

NOT NULL

starter_code

TEXT

NULL

expected_output

JSONB

NULL

test_code

TEXT

NULL

difficulty

VARCHAR(30)

NULL

max_score

NUMERIC(6,2)

NOT NULL

created_at

TIMESTAMP

NOT NULL

Supported frameworks:

qiskit
pennylane
cirq

13. code_submissions

Stores code submitted by learners.

Column

Type

Constraints

submission_id

UUID

PK

challenge_id

UUID

FK → coding_challenges.challenge_id

user_id

UUID

FK → users.user_id

code

TEXT

NOT NULL

framework

VARCHAR(30)

NOT NULL

execution_output

TEXT

NULL

error_message

TEXT

NULL

score

NUMERIC(6,2)

NULL

passed

BOOLEAN

NULL

execution_time_ms

INTEGER

NULL

submitted_at

TIMESTAMP

NOT NULL

14. circuits

Stores quantum circuits created by users.

Column

Type

Constraints

circuit_id

UUID

PK

user_id

UUID

FK → users.user_id

name

VARCHAR(200)

NOT NULL

description

TEXT

NULL

num_qubits

INTEGER

NOT NULL

num_classical_bits

INTEGER

DEFAULT 0

source_type

VARCHAR(20)

NOT NULL

framework

VARCHAR(30)

NULL

circuit_data

JSONB

NOT NULL

created_at

TIMESTAMP

NOT NULL

updated_at

TIMESTAMP

NOT NULL

source_type:

visual
code

circuit_data stores the React Flow / circuit representation.

Example:

{
  "nodes": [
    {
      "gate": "H",
      "qubit": 0,
      "position": 1
    },
    {
      "gate": "CNOT",
      "control": 0,
      "target": 1,
      "position": 2
    }
  ]
}

15. quantum_gates

Master catalog of supported quantum gates.

Column

Type

Constraints

gate_id

UUID

PK

name

VARCHAR(50)

UNIQUE, NOT NULL

symbol

VARCHAR(20)

NOT NULL

description

TEXT

NULL

num_qubits

INTEGER

NOT NULL

matrix

JSONB

NULL

Examples:

H
X
Y
Z
CNOT
Toffoli
SWAP
Measurement

16. circuit_gates

Stores the actual gates placed inside circuits.

Column

Type

Constraints

circuit_gate_id

UUID

PK

circuit_id

UUID

FK → circuits.circuit_id

gate_id

UUID

FK → quantum_gates.gate_id

qubit_position

INTEGER

NOT NULL

control_qubit

INTEGER

NULL

target_qubit

INTEGER

NULL

gate_order

INTEGER

NOT NULL

parameters

JSONB

NULL

This supports circuits such as:

Q0 ── H ──●── M
          │
Q1 ───────X── M

17. circuit_versions

Maintains circuit/code history.

Column

Type

Constraints

version_id

UUID

PK

circuit_id

UUID

FK → circuits.circuit_id

version_number

INTEGER

NOT NULL

source_type

VARCHAR(20)

NOT NULL

code

TEXT

NULL

circuit_data

JSONB

NULL

created_by

UUID

FK → users.user_id

created_at

TIMESTAMP

NOT NULL

Unique constraint:

(circuit_id, version_number)

18. simulation_runs

Stores executions of quantum circuits.

Column

Type

Constraints

simulation_id

UUID

PK

circuit_id

UUID

FK → circuits.circuit_id

user_id

UUID

FK → users.user_id

backend

VARCHAR(50)

NOT NULL

shots

INTEGER

NULL

status

VARCHAR(30)

NOT NULL

execution_time_ms

INTEGER

NULL

started_at

TIMESTAMP

NOT NULL

completed_at

TIMESTAMP

NULL

error_message

TEXT

NULL

Backends:

qiskit_aer
pennylane
cirq

The architecture uses Qiskit Aer, PennyLane, and Cirq through a modular simulator architecture.

19. simulation_results

Stores simulation outputs.

Column

Type

Constraints

result_id

UUID

PK

simulation_id

UUID

FK → simulation_runs.simulation_id

measurement_counts

JSONB

NULL

probabilities

JSONB

NULL

state_vector

JSONB

NULL

bloch_data

JSONB

NULL

circuit_diagram

TEXT

NULL

created_at

TIMESTAMP

NOT NULL

Example measurement_counts:

{
  "00": 498,
  "11": 502
}

Example probabilities:

{
  "00": 0.498,
  "11": 0.502
}

20. ai_conversations

Stores AI tutor conversations.

Column

Type

Constraints

conversation_id

UUID

PK

user_id

UUID

FK → users.user_id

circuit_id

UUID

FK → circuits.circuit_id, NULL

title

VARCHAR(200)

NULL

created_at

TIMESTAMP

NOT NULL

updated_at

TIMESTAMP

NOT NULL

21. ai_messages

Stores individual AI/user messages.

Column

Type

Constraints

message_id

UUID

PK

conversation_id

UUID

FK → ai_conversations.conversation_id

sender_type

VARCHAR(20)

NOT NULL

message

TEXT

NOT NULL

context_data

JSONB

NULL

created_at

TIMESTAMP

NOT NULL

sender_type:

user
assistant
system

context_data can store:

{
  "circuit_id": "uuid",
  "simulation_id": "uuid",
  "code": "...",
  "error": "..."
}

22. learning_recommendations

Stores personalized learning recommendations.

Column

Type

Constraints

recommendation_id

UUID

PK

user_id

UUID

FK → users.user_id

module_id

UUID

FK → learning_modules.module_id

reason

TEXT

NOT NULL

priority

INTEGER

NULL

status

VARCHAR(30)

NOT NULL

created_at

TIMESTAMP

NOT NULL

completed_at

TIMESTAMP

NULL

Example:

User repeatedly performs poorly in Entanglement.

Recommendation:
Review Entanglement module.
Try Bell State tutorial.
Complete practice questions.

23. user_gamification

Stores the user's gamification statistics.

Column

Type

Constraints

user_id

UUID

PK, FK → users.user_id

xp

INTEGER

DEFAULT 0

level

INTEGER

DEFAULT 1

current_streak

INTEGER

DEFAULT 0

longest_streak

INTEGER

DEFAULT 0

updated_at

TIMESTAMP

NOT NULL

24. badges

Master list of achievements.

Column

Type

Constraints

badge_id

UUID

PK

name

VARCHAR(100)

UNIQUE, NOT NULL

description

TEXT

NOT NULL

icon_url

TEXT

NULL

requirement_type

VARCHAR(50)

NOT NULL

requirement_value

INTEGER

NULL

25. user_badges

Many-to-many relationship between users and badges.

Column

Type

Constraints

user_badge_id

UUID

PK

user_id

UUID

FK → users.user_id

badge_id

UUID

FK → badges.badge_id

earned_at

TIMESTAMP

NOT NULL

Unique constraint:

(user_id, badge_id)

26. course_enrollments

Tracks students enrolled in courses.

Column

Type

Constraints

enrollment_id

UUID

PK

course_id

UUID

FK → courses.course_id

user_id

UUID

FK → users.user_id

status

VARCHAR(30)

NOT NULL

enrolled_at

TIMESTAMP

NOT NULL

Unique constraint:

(course_id, user_id)

27. course_assignments

Allows instructors to assign learning content or assessments.

Column

Type

Constraints

assignment_id

UUID

PK

course_id

UUID

FK → courses.course_id

module_id

UUID

FK → learning_modules.module_id, NULL

assessment_id

UUID

FK → assessments.assessment_id, NULL

assigned_by

UUID

FK → users.user_id

due_date

TIMESTAMP

NULL

created_at

TIMESTAMP

NOT NULL

28. shared_resources

Supports circuit/code/project sharing.

Column

Type

Constraints

share_id

UUID

PK

user_id

UUID

FK → users.user_id

circuit_id

UUID

FK → circuits.circuit_id, NULL

resource_type

VARCHAR(30)

NOT NULL

title

VARCHAR(200)

NOT NULL

description

TEXT

NULL

share_token

VARCHAR(100)

UNIQUE, NOT NULL

visibility

VARCHAR(20)

NOT NULL

created_at

TIMESTAMP

NOT NULL

expires_at

TIMESTAMP

NULL

resource_type:

circuit
code
project

visibility:

private
link
public

29. Main Relationships

Parent

Relationship

Child

users

1

courses

courses

1

learning_modules

users

1

module_progress

learning_modules

1

module_progress

learning_modules

1

assessments

assessments

1

questions

questions

1

question_options

assessments

1

assessment_attempts

users

1

assessment_attempts

assessment_attempts

1

question_answers

learning_modules

1

coding_challenges

coding_challenges

1

code_submissions

users

1

code_submissions

users

1

circuits

circuits

1

circuit_gates

quantum_gates

1

circuit_gates

circuits

1

circuit_versions

circuits

1

simulation_runs

simulation_runs

1:1

simulation_results

users

1

ai_conversations

ai_conversations

1

ai_messages

users

1

learning_recommendations

learning_modules

1

learning_recommendations

users

1:1

user_gamification

users

N

badges through user_badges

users

N

courses through course_enrollments

users

1

shared_resources

circuits

1

shared_resources

30. PostgreSQL Design Notes

Primary Keys

Use UUIDs:

UUID PRIMARY KEY DEFAULT gen_random_uuid()

JSONB

Use JSONB for dynamic quantum data:

circuits.circuit_data

circuit_gates.parameters

simulation_results.measurement_counts

simulation_results.probabilities

simulation_results.state_vector

simulation_results.bloch_data

ai_messages.context_data

Timestamps

Use:

TIMESTAMP WITH TIME ZONE

for application timestamps.

Important Indexes

Create indexes on:

users.email
learning_modules.course_id
module_progress.user_id
module_progress.module_id
assessments.module_id
assessment_attempts.user_id
circuits.user_id
circuit_gates.circuit_id
simulation_runs.circuit_id
simulation_runs.user_id
ai_conversations.user_id
ai_messages.conversation_id
code_submissions.user_id
course_enrollments.user_id
shared_resources.share_token

31. Simplified MVP Model

For the hackathon MVP, you do not have to implement every table immediately.

Start with:

users
courses
learning_modules
module_progress

assessments
questions
question_options
assessment_attempts

circuits
quantum_gates
circuit_gates
simulation_runs
simulation_results

ai_conversations
ai_messages

coding_challenges
code_submissions

Then add:

user_gamification
badges
user_badges
course_enrollments
course_assignments
shared_resources
learning_recommendations
circuit_versions

after the core workflow is working.

This keeps the database manageable while still leaving room for the instructor dashboard, gamification, collaboration, AI personalization, and advanced simulation features described in the project roadmap.