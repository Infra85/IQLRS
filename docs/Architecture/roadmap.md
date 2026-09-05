# AI-Based Interactive Quantum Algorithm Learning Platform — Roadmap

## Tech Stack (Recommended for Hackathon Speed)

| Layer | Tech |
|-------|------|
| Frontend | **Next.js** (React) + TypeScript |
| UI Components | shadcn/ui + Tailwind CSS |
| Circuit Builder | React Flow (drag-and-drop) |
| Code Editor | Monaco Editor (VS Code in browser) |
| Quantum Simulation | Python backend — Qiskit, PennyLane, Cirq |
| Backend API | **FastAPI** (Python) |
| AI Tutor | Claude API (or OpenAI) |
| Database | PostgreSQL + Prisma ORM |
| Auth | NextAuth.js |
| Deployment | Vercel (frontend) + Railway/Render (backend) |

---

## Team Assignments

### P1 — Frontend Lead + Circuit Builder
**Owns:** Deliverables 2, 5
- Drag-and-drop quantum circuit builder (React Flow)
- Gate palette (H, X, Y, Z, CNOT, Toffoli, etc.)
- Bloch sphere visualization (Three.js or a library like `bloch-sphere`)
- Probability bar charts, state vector display
- Circuit diagram rendering from user-built circuits

### P2 — Code Editor + Simulation Integration
**Owns:** Deliverables 3, 4, 13
- Monaco Editor with Qiskit/PennyLane/Cirq syntax support
- "Run" button that sends code to backend for execution
- Multi-backend architecture: FastAPI routes that dispatch to Qiskit Aer, PennyLane default.qubit, Cirq simulator
- Returns measurement results, statevectors, circuit diagrams back to frontend
- Sandboxed execution (subprocess or Docker)

### P3 — AI Tutor + Debugging Engine
**Owns:** Deliverables 6, 7, 8
- AI chat panel (Claude/OpenAI API integration)
- System prompts specialized for quantum computing tutoring
- Context-aware: feed current circuit/code into AI for explanations
- Error detection: parse simulation errors, suggest fixes
- Circuit optimization suggestions (gate reduction, simplification)
- Personalized learning path: track weak areas from assessments, recommend next modules

### P4 — Learning Modules + Content
**Owns:** Deliverables 1, 9
- Write/curate structured learning content (MDX or JSON-driven):
  - Module 1: Classical vs Quantum Computing
  - Module 2: Qubits, Superposition, Measurement
  - Module 3: Quantum Gates (single-qubit, multi-qubit)
  - Module 4: Entanglement & Bell States
  - Module 5: Deutsch-Jozsa Algorithm
  - Module 6: Grover's Search
  - Module 7: Quantum Teleportation
  - Module 8: Shor's Algorithm (overview)
- Build quiz engine: MCQ, circuit-building challenges, code challenges
- Each module ends with hands-on exercises tied to the circuit builder

### P5 — User System + Dashboards + Gamification
**Owns:** Deliverables 10, 11, 12
- Auth system (NextAuth — email/Google login)
- Database schema: users, progress, scores, submissions
- Learner dashboard: progress bars, completed modules, scores, streaks, badges
- Instructor dashboard: view all learners, assign modules, see class-wide analytics
- Collaborative features: share circuit/code via link, public project gallery
- Gamification: XP points, level system, achievement badges

### P6 — Backend Infrastructure + Deployment + Docs
**Owns:** Deliverables 13, 14, 15
- FastAPI project setup, API design, CORS, middleware
- Database setup (PostgreSQL + migrations)
- Docker Compose for local dev (frontend + backend + DB)
- CI/CD pipeline (GitHub Actions — lint, test, build)
- Deployment to Vercel + Railway/Render
- Write: README, API docs (auto-generated from FastAPI), architecture diagram, setup guide
- Build the demo flow: Learn → Build → Code → Simulate → Visualize → AI → Assess

---

## Timeline 

| Day | Focus | Who |
|-----|-------|-----|
| **Day -** | Repo setup, tech stack installed, DB schema, basic Next.js + FastAPI skeleton | P6 leads, everyone sets up |
| **Day -** | Circuit builder MVP, code editor shell, AI chat shell, first 2 learning modules written | P1, P2, P3, P4 |
| **Day -** | Qiskit simulation working end-to-end, circuit → results displayed, auth working | P2, P1, P5 |
| **Day -** | AI tutor connected with context, quizzes working, dashboards started | P3, P4, P5 |
| **Day -** | Bloch sphere viz, multi-backend support, all modules drafted | P1, P2, P4 |
| **Day -** | Gamification, instructor dashboard, collaborative sharing, optimization suggestions | P5, P3, P1 |
| **Day -** | Integration testing, deployment, documentation, demo prep | Everyone |

---

## Delivery Table (Expected Deliverables)

| S. No. | Deliverable | Description | Owner |
|--------|-------------|-------------|-------|
| 1 | **Interactive Learning Modules** | Structured modules covering quantum computing fundamentals, qubits, superposition, entanglement, quantum gates, circuits, and standard quantum algorithms. | P4 |
| 2 | **Visual Quantum Circuit Builder** | Drag-and-drop interface allowing users to create, modify, and visualize quantum circuits without requiring prior programming knowledge. | P1 |
| 3 | **Integrated Quantum Code Editor** | In-browser coding environment supporting popular quantum frameworks such as Qiskit, PennyLane, and Cirq, with syntax assistance and execution support. | P2 |
| 4 | **Quantum Circuit Simulator** | Real-time simulation of user-created circuits using multiple supported simulation backends, with execution results and measurement probabilities. | P2 |
| 5 | **Quantum State Visualization** | Interactive visualization of quantum states using Bloch spheres, probability distributions, state vectors, circuit diagrams, and measurement outcomes. | P1 |
| 6 | **AI Quantum Tutor** | AI assistant capable of explaining quantum concepts, answering questions, generating example circuits/code, identifying errors, and providing step-by-step guidance. | P3 |
| 7 | **AI-Based Debugging & Optimization** | Detection of common circuit/code errors with suggestions for corrections, circuit simplification, and performance improvements. | P3 |
| 8 | **Personalized Learning Path** | Adaptive recommendations based on the learner's progress, assessment performance, strengths, and areas requiring improvement. | P3 |
| 9 | **Assessments & Coding Challenges** | Quizzes, circuit-building exercises, algorithm challenges, and practical tasks to evaluate understanding and programming skills. | P4 |
| 10 | **Progress Tracking & Gamification** | Learner dashboard showing completed modules, scores, challenges, learning progress, and achievements. | P5 |
| 11 | **Instructor Dashboard** | Tools for instructors to monitor learner performance, assign modules/challenges, review progress, and identify learning gaps. | P5 |
| 12 | **Collaborative Learning Features** | Support for sharing circuits, code, learning resources, and projects to encourage collaborative experimentation and peer learning. | P5 |
| 13 | **Multi-Backend Architecture** | Modular backend architecture allowing integration with multiple quantum simulators and, where available, future access to real quantum hardware. | P2, P6 |
| 14 | **Deployment & Documentation** | Fully deployed web platform with user documentation, system architecture documentation, API documentation, and setup instructions. | P6 |
| 15 | **Demonstration Prototype** | End-to-end working prototype demonstrating the complete workflow: **Learn → Build → Code → Simulate → Visualize → Get AI Guidance → Assess**. | P6 |

---

## GitHub Repo Structure

```
quantum-learn/
├── .github/
│   └── workflows/
│       └── ci.yml                    # lint + test + build
├── frontend/                         # Next.js app
│   ├── src/
│   │   ├── app/                      # Next.js app router
│   │   │   ├── (auth)/               # login, register
│   │   │   ├── learn/                # learning modules
│   │   │   ├── builder/              # circuit builder page
│   │   │   ├── editor/               # code editor page
│   │   │   ├── dashboard/            # learner dashboard
│   │   │   ├── instructor/           # instructor dashboard
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── circuit-builder/      # React Flow circuit components
│   │   │   ├── code-editor/          # Monaco editor wrapper
│   │   │   ├── ai-tutor/            # chat panel
│   │   │   ├── visualizations/       # Bloch sphere, prob charts
│   │   │   ├── learning/             # module renderer, quiz components
│   │   │   └── ui/                   # shadcn components
│   │   ├── lib/                      # API client, utils, auth config
│   │   └── content/                  # MDX/JSON learning modules
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── backend/                          # FastAPI app
│   ├── app/
│   │   ├── main.py                   # FastAPI entry
│   │   ├── api/
│   │   │   ├── circuits.py           # circuit simulation endpoints
│   │   │   ├── code.py               # code execution endpoints
│   │   │   ├── ai.py                 # AI tutor endpoints
│   │   │   ├── auth.py               # auth endpoints
│   │   │   ├── progress.py           # progress/scores endpoints
│   │   │   └── collaborate.py        # sharing endpoints
│   │   ├── services/
│   │   │   ├── simulators/
│   │   │   │   ├── qiskit_runner.py
│   │   │   │   ├── pennylane_runner.py
│   │   │   │   └── cirq_runner.py
│   │   │   ├── ai_tutor.py
│   │   │   └── sandbox.py            # safe code execution
│   │   ├── models/                   # SQLAlchemy/Prisma models
│   │   ├── schemas/                  # Pydantic schemas
│   │   └── core/                     # config, security, db
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
├── docker-compose.yml
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── setup.md
├── README.md
├── .gitignore
└── LICENSE
```
