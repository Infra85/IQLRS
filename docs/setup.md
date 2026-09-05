# Setup Guide

## Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 16+
- Docker & Docker Compose (optional but recommended)

## Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/quantum-learn.git
cd quantum-learn

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Option 2: Manual Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/quantumlearn"
export AI_API_KEY="your-api-key"

# Create database
createdb quantumlearn

# Run the server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

## Running Tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm run lint
```
