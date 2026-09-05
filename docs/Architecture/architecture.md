# Architecture

## Overview

Quantum Learn is a monorepo with two main services:

```
┌─────────────────┐     HTTP/JSON     ┌─────────────────┐
│    Frontend      │ ───────────────► │     Backend      │
│   (Next.js)      │ ◄─────────────── │    (FastAPI)     │
│   Port 3000      │                  │    Port 8000     │
└─────────────────┘                  └────────┬────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              │               │               │
                        ┌─────▼─────┐  ┌──────▼──────┐ ┌─────▼─────┐
                        │  Qiskit   │  │ PennyLane   │ │   Cirq    │
                        │   Aer     │  │ default.qb  │ │ Simulator │
                        └───────────┘  └─────────────┘ └───────────┘
                              │
                        ┌─────▼─────┐
                        │ PostgreSQL │
                        │   (DB)     │
                        └───────────┘
```

## Frontend

- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + shadcn/ui
- **Circuit Builder:** React Flow for drag-and-drop
- **Code Editor:** Monaco Editor
- **3D Visualization:** React Three Fiber (Bloch spheres)

## Backend

- **Framework:** FastAPI
- **Database:** PostgreSQL via SQLAlchemy
- **Quantum Simulators:** Qiskit Aer, PennyLane, Cirq (modular runner pattern)
- **AI Integration:** Claude/OpenAI API via service layer
- **Code Execution:** Sandboxed subprocess

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/circuits/simulate` | Simulate a quantum circuit |
| POST | `/api/code/execute` | Execute quantum code |
| POST | `/api/ai/chat` | AI tutor chat |
| POST | `/api/ai/debug` | AI-powered debugging |
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login |
| GET | `/api/progress/{user_id}` | Get learning progress |
| POST | `/api/progress/{user_id}/update` | Update progress |
| POST | `/api/collaborate/share` | Share a resource |
| GET | `/api/collaborate/{share_id}` | Get shared resource |
