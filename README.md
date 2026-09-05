# Quantum Learn

AI-Based Interactive Quantum Algorithm Learning Platform.

Learn, build, simulate, and visualize quantum algorithms with AI-powered guidance.

## Features

- **Interactive Learning Modules** — Structured content covering quantum computing fundamentals through advanced algorithms
- **Visual Circuit Builder** — Drag-and-drop quantum circuit design
- **Code Editor** — In-browser coding with Qiskit, PennyLane, and Cirq support
- **Circuit Simulator** — Real-time simulation with multiple backends
- **State Visualization** — Bloch spheres, probability distributions, state vectors
- **AI Tutor** — Concept explanations, error detection, optimization suggestions
- **Assessments** — Quizzes, coding challenges, and progress tracking
- **Dashboards** — Learner and instructor analytics

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


## Project Structure

```
quantum-learn/
├── frontend/          # Next.js app
├── backend/           # FastAPI app
├── docs/              # Documentation
├── docker-compose.yml
└── README.md
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.



