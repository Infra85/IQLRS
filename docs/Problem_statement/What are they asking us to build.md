# What are they asking us to build?

Think of it like:

"Duolingo +Figma +Google Classroom +ChatGPT + VS Code + Quantum Simulator, all in one website.(FOR QUANTUM COMPUTING)"

## Demo 1:
For student.

🧩 Build Quantum Circuits

The student should be able to create circuits in two ways.

### Method 1 — Drag & Drop

For example:

Qubit 0 ─── H ───●──── M
                  │
Qubit 1 ──────────X──── M

The user can drag gates onto qubits.

For example:

H gate
X gate
Y gate
Z gate
CNOT
Measurement

### Method 2 — Code

The student can write quantum code.

For example, conceptually:

qc.h(0)
qc.cx(0, 1)
qc.measure_all()

Your platform executes the circuit and shows the result.

The problem statement explicitly expects both graphical drag-and-drop and code-based circuit creation.

2. Quantum Simulation

This is one of the most important parts.

Suppose the student creates:

Q0 ── H ──●──
          │
Q1 ───────X──

Your system should simulate it.

The result could show something like:

Measurement Results

00 → 49.8%
11 → 50.2%

The user should be able to understand what happened rather than just seeing raw numbers.

The problem statement expects support for multiple quantum frameworks/backends such as Qiskit, PennyLane, Cirq and Qbraid.

📊 3. Visualization

This is another major feature.

Instead of just showing:

00 = 50%
11 = 50%

you can visually explain the quantum state.

The expected solution mentions things such as:

Bloch Sphere

For a single qubit:

        |0>
         ↑
         |
         ●
       /   \
      /     \
     ───────→
         |
         ↓
        |1>

The student can see how applying different gates changes the quantum state.

- Measurement Histogram

Something like:

Probability

50% | ███████████       █
    | ███████████       █
    | ███████████       █
 0% |_____________________
       00              11
- State Vector

Show the mathematical representation of the quantum state.

4. AI Assistant — THIS IS A BIG OPPORTUNITY

This is where our project can become much more interesting.

The problem specifically asks for AI-assisted tutoring.

Imagine the student writes:

"Why did applying H gate produce these results?"

Your AI could respond:

"The Hadamard gate puts the qubit into an equal superposition of |0⟩ and |1⟩. Therefore, when measured, each outcome has approximately a 50% probability."

AI can do several things
🧑‍🏫 AI Tutor

Student:

Explain quantum entanglement like I'm a beginner.

AI:

Imagine two quantum coins that become connected in such a way that measuring one gives information about the other...

🐛 Debugging

Student creates an incorrect circuit.

Your AI could say:

⚠️ Possible issue
You are applying a CNOT gate to qubit 1 before initializing the control qubit.

Or explain why the output isn't what they expected.

💡 Code Generation

Student:

"Create a Bell state using Qiskit."

AI generates the corresponding quantum circuit/code.

🔧 Optimization

The AI could inspect a circuit and suggest:

You can reduce the number of gates in this circuit by replacing these operations with an equivalent gate sequence.

🎓 Personalized Learning

Suppose a student repeatedly gets questions about entanglement wrong.

Your system can recommend:

Your weak area:
🔴 Entanglement

Recommended:
- Review Entanglement
- Try Bell State Tutorial
- Complete 5 practice questions

5. Learning Module

The platform isn't supposed to be just a simulator.

It should also have structured educational content.

For example:

COURSE

01  Introduction to Quantum Computing
       ↓
02  Qubits
       ↓
03  Quantum States
       ↓
04  Quantum Gates
       ↓
05  Superposition
       ↓
06  Entanglement
       ↓
07  Quantum Circuits
       ↓
08  Quantum Algorithms

The problem statement specifically mentions algorithms such as:

Deutsch-Jozsa
Grover
QAOA
VQE

along with theoretical explanations and interactive examples.

6. Assessment System

You also need an education/assessment component.

For example:

Quiz

What does an H gate do?

○ A. Measures the qubit
○ B. Creates superposition
○ C. Deletes the qubit
○ D. Entangles two qubits

Then:

Correct! ✅

Score: 8/10

Coding Challenges

For example:

Create a Bell state using a Hadamard and CNOT gate.

The system executes the student's circuit/code and checks whether the expected result was achieved.

7. Progress Tracking

Each student should have a dashboard.

Something like:

--------------------------------
       MY DASHBOARD
--------------------------------

Quantum Fundamentals    ████████░░ 80%

Quantum Gates            ██████░░░░ 60%

Entanglement             ████░░░░░░ 40%

Algorithms               ██░░░░░░░░ 20%

--------------------------------

Quiz Score       82%
Challenges       12 / 20
Learning Streak  7 days
--------------------------------

The problem statement also expects progress tracking and performance analytics.

8. Instructor Dashboard

The expected solution also mentions instructor dashboards.

So you can have:

Student
Learn
 ↓
Practice
 ↓
Build Circuit
 ↓
Simulate
 ↓
Get AI Help
 ↓
Assessment
 ↓
Track Progress
Instructor
Create Course
     ↓
Create Quiz
     ↓
Create Coding Challenge
     ↓
Monitor Students
     ↓
View Performance

9. What your final website could look like

A possible architecture:

                    ┌───────────────────────┐
                    │       FRONTEND        │
                    │   React / Next.js     │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        Learning System    Circuit Builder    AI Tutor
              │                 │                 │
              │                 ▼                 │
              │          Quantum Simulator        │
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │       BACKEND         │
                    │   FastAPI / Node.js   │
                    └───────────┬───────────┘
                                │
                ┌───────────────┼────────────────┐
                ▼               ▼                ▼
             Database      AI Service      Quantum Engines
             PostgreSQL    LLM API         Qiskit/PennyLane

🧑‍💻 10. What should YOUR team actually build?

This is important for a hackathon.

The problem statement is very broad. You don't necessarily need to build an enormous production platform during the hackathon.

I'd divide it into:

🔥 MUST HAVE — MVP
1. Login
Student
Instructor
2. Learning Modules

At least:

Qubits
Quantum Gates
Superposition
Entanglement
3. Quantum Circuit Builder

Drag and drop:

H
X
Y
Z
CNOT
Measurement
4. Code Editor

Allow users to write quantum code.

5. Simulator

Execute the circuit and return:

Measurement results
Probabilities
State information
6. Visualization

At minimum:

Circuit diagram
Measurement histogram
Bloch sphere
7. AI Tutor

The student should be able to ask:

"Explain this circuit."

and get an explanation.

8. Quiz

Basic quantum-computing questions.

9. Progress Dashboard

Track:

Courses completed
Quiz scores
Coding challenges
Weak areas

⭐ Features that could impress the judges

Once the MVP works, these are where you can differentiate yourselves.

🔥 AI Circuit Explainer

This could be your signature feature.

Student creates:

q0 ── H ──●── M
          │
q1 ───────X── M

Then presses:

"Explain My Circuit"

AI produces:

Step 1:
H was applied to q0.

This creates superposition.

Step 2:
CNOT connects q0 and q1.

This creates entanglement.

Step 3:
Both qubits are measured.

Expected outcomes:
00 ≈ 50%
11 ≈ 50%

That directly combines the AI + quantum + education aspects of the problem.

If a judge asks:

"What exactly are you building?"

You can say:

"We are building an AI-powered interactive quantum computing education platform where students don't just read about quantum computing—they learn by building and running quantum circuits. Users can create circuits using drag-and-drop or code, simulate them using quantum frameworks, visualize quantum states and measurement results, and receive real-time AI tutoring, debugging and optimization suggestions. The platform also tracks learning progress through quizzes and coding challenges."

🎯 The core idea

Think of your project as this loop:

             ┌──────────────┐
             │    LEARN     │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │    BUILD     │
             │   CIRCUIT    │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │   SIMULATE   │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │  VISUALIZE   │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │  AI EXPLAINS │
             │  & DEBUGS    │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │   PRACTICE   │
             │    & QUIZ    │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │   PROGRESS   │
             └──────────────┘
                    │
                    └──────────→ LEARN AGAIN
## Demo 2:
