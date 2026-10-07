# Architecture

## Current curriculum path

The eight-module source is `backend/data/modules.json`. The curriculum service validates it and the existing migration seeds JSON text into `LearningModule.content`, using unchanged UUID5 identifiers. An exact-content fingerprint permits upgrading the previous unmodified publisher bundle; custom rows and learner activity are retained. Metadata needs no schema change.

Lesson pages render the generated `frontend/src/app/learn/modules.ts`, not a database fetch. Run `node frontend/scripts/sync-curriculum.cjs` after source edits; frontend tests enforce equality with server scoring data. Quiz submissions use `/api/progress/lessons/{number}/quiz`; personal progress uses `/api/progress/me`. Planned experiment/challenge metadata has no runtime in this phase. See [the scientific review](../CURRICULUM_SCIENTIFIC_REVIEW.md) for deployment and compatibility details.

The remaining diagram and subsystem list below describe the original design, not current implemented capability. The current engine is documented in [Simulator V2](../SIMULATOR_V2.md); Code Lab and collaboration are unreleased.

## Original design overview

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
