# INTELLIGENT QUANTUM LEARNING AND RESEARCH SYSTEM

AI-Based Interactive Quantum Algorithm Learning Platform.

Learn, build, simulate, and visualize quantum algorithms with AI-powered guidance.

v.1- For student: Simulation only avaliable according to the learning module.

v.2- For instructure, researchers: High end simulation available, for complex computing, through code.

## Features v.1

- **Interactive Learning Modules** — Structured content covering quantum computing fundamentals through advanced algorithms
- **Visual Circuit Builder** — Drag-and-drop quantum circuit design
- **Code Editor** — In-browser coding with Qiskit, PennyLane, and Cirq support
- **Circuit Simulator** — Real-time simulation with multiple backends
- **State Visualization** — Bloch spheres, probability distributions, state vectors
- **AI Tutor** — Concept explanations, error detection, optimization suggestions
- **Assessments** — Quizzes, coding challenges, and progress tracking
- **Dashboards** — Learner and instructor analytics

## Features v.2

- More freedom for quantum simulation.
## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, Tailwind CSS, shadcn/ui |
| Circuit Builder | React Flow |
| Code Editor | Monaco Editor |
| Backend | FastAPI (Python) |
| Quantum Engines | Qiskit, PennyLane, Cirq |
| AI | Claude / OpenAI API |
| Database | PostgreSQL |

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL
- Docker (optional)

### Quick Start

```bash
# Clone the repo
git clone 
cd quantum-learn

# Start everything with Docker
docker compose up

# Or run individually:

# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```


### Backend environment and email verification

Copy `.env.example` to `.env` at the repository root before starting locally or
with Compose. The backend loads that file regardless of its working directory;
an optional `backend/.env` overrides it, and process environment variables take
precedence over both. Compose forwards the SMTP variables to the backend.

The default local database is `quantumlearn`, matching the database already
provisioned by Compose (local host `localhost`, container host `db`). If your
existing local database is named `IQLRS`, set `DATABASE_URL` in your ignored
`.env` to point to it. No database or existing Docker volume needs to be renamed.

The app can start without SMTP credentials; registration returns a clear HTTP
503 until email is configured. To enable registration, set `SMTP_EMAIL` to your
Gmail sender address and `SMTP_PASSWORD` to its SMTP app password in `.env` or
your deployment environment, then restart the backend. Never commit credentials.
The sender uses Gmail on port 587 with certificate-verified STARTTLS.

Successful registration still requires the emailed OTP before login. Failed
email delivery rolls back new accounts. An existing unverified account can retry
registration using its original password to send a fresh OTP; its name and password
are preserved, and failed retries preserve the previous OTP. Verified accounts
continue to receive the existing duplicate-email error. SMTP acceptance and a
database commit cannot be atomic: if the database commit fails after sending,
the received code may not work and registration must be retried.

## Project Structure

```
quantum-learn/
├── frontend/          # Next.js app
├── backend/           # FastAPI app
├── docs/              # Documentation
├── docker-compose.yml
└── README.md
```

See [docs/Architecture/architecture.md](docs/Architecture/architecture.md) for detailed architecture documentation.

