# INTELLIGENT QUANTUM LEARNING AND RESEARCH SYSTEM

AI-Based Interactive Quantum Algorithm Learning Platform.

Learn, build, simulate, and visualize quantum algorithms with AI-powered guidance.

v.1- For student: Simulation only avaliable according to the learning module.

v.2- For instructure, researchers: High end simulation available, for complex computing, through code.

## Features v.1

- **Interactive Learning Modules** — Structured content covering quantum computing fundamentals through advanced algorithms
- **Visual Circuit Builder** — Drag-and-drop quantum circuit design
- **Code Editor (unreleased)** — Source retained; execution is not exposed
- **Circuit Simulator** — Real-time simulation with multiple backends
- **State Visualization** — Bloch spheres, probability distributions, state vectors
- **AI Tutor** — Concept explanations, error detection, optimization suggestions
- **Assessments** — Quizzes, coding challenges, and progress tracking
- **Dashboard** — Persisted learner activity; instructor analytics is unreleased

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

- Node.js 22+
- Python 3.12+
- PostgreSQL
- Docker (optional)

### Quick Start

```bash
# Clone the repo
git clone 
cd quantum-learn

# Start everything with Docker
docker compose up -d db
docker compose --profile tools run --rm migrate
docker compose up -d backend frontend

# Or run individually:

# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
pip install -r requirements.txt
python -m app.migrate
uvicorn app.main:app --reload
```


### Production deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for required configuration, the
versioned PostgreSQL migration, legacy data preservation, email DNS requirements,
startup commands, and verified limitations. Run migrations before starting the API.
The code lab, instructor analytics, and collaboration are unreleased and hidden.
Signed-in simulations, quiz progress, dashboards, and AI conversations use real
persisted data. Guest circuit experiments remain available without saving.

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

