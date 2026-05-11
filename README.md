# Project Management MVP - Setup Guide

## Overview

This is a Project Management MVP application with a Next.js frontend and FastAPI backend, containerized with Docker.

## Prerequisites

- Docker and Docker Compose installed
- Node.js 20+ (for local development without Docker)
- Python 3.12+ (for local backend development)

## Quick Start

### Option 1: Using Docker (Recommended)

#### Windows (PowerShell)

```powershell
# Make sure you're in the project root, then:
.\scripts\start.ps1
```

#### Windows (Command Prompt)

```batch
scripts\start.bat
```

#### Mac/Linux

```bash
chmod +x ./scripts/start.sh ./scripts/stop.sh
./scripts/start.sh
```

The start script will:

1. Check Docker is running
2. Build the frontend (Next.js static export)
3. Build the Docker image (multi-stage: frontend build + backend runtime)
4. Start the container
5. Wait for the service to be ready

After running the start script, the application will be available at:

- **Frontend (Kanban Board)**: http://localhost:8000
- **API Test**: http://localhost:8000/api/test

To stop:

- **Windows (PowerShell)**: `.\scripts\stop.ps1`
- **Windows (Command Prompt)**: `scripts\stop.bat`
- **Mac/Linux**: `./scripts/stop.sh`

### Option 2: Local Development (Without Docker)

#### Prerequisites

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

#### Start Backend

```bash
cd backend
python -m uvicorn main:app --reload
```

#### Start Frontend (in another terminal)

```bash
cd frontend
npm run dev
```

Backend runs on http://localhost:8000
Frontend dev server runs on http://localhost:3000

## Environment Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```
OPENAI_API_KEY=your_key_here
PORT=8000
DATABASE_URL=sqlite:///./pm.db
```

## Running Tests

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm run test
```

### E2E Tests

```bash
cd frontend
npm run test:e2e
```

## Docker Commands

```bash
# Build the image
docker-compose build

# Start services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove everything (including volumes)
docker-compose down -v
```

## Project Structure

```
.
├── frontend/              # Next.js frontend app
├── backend/               # FastAPI backend
│   ├── main.py           # Main application
│   ├── requirements.txt   # Python dependencies
│   ├── pyproject.toml     # Project metadata
│   └── tests/             # Backend tests
├── scripts/               # Start/stop scripts
├── docs/                  # Documentation
├── Dockerfile             # Docker build configuration
├── docker-compose.yml     # Docker Compose configuration
├── .env.example          # Environment template
└── .gitignore            # Git ignore rules
```

## Part 2-3 Status

### Part 2: Docker & Backend Scaffolding ✓ COMPLETE

- ✓ Dockerfile with Python backend
- ✓ docker-compose.yml configuration
- ✓ FastAPI backend with test endpoint
- ✓ Start/stop scripts for Windows, Mac, and Linux
- ✓ Environment configuration (.env)
- ✓ Backend unit tests

### Part 3: Frontend Integration ✓ COMPLETE

- ✓ Next.js static export configuration (`next.config.ts`)
- ✓ FastAPI serving frontend static files
- ✓ Multi-stage Docker build (frontend + backend)
- ✓ CORS middleware for API access
- ✓ Start scripts include frontend build step
- ✓ Frontend integration tests
- ✓ Kanban board displays at root `/`

### How to Verify

1. Run `.\scripts\start.bat` (or equivalent for your OS)
2. Open http://localhost:8000 in browser:
   - You should see the Kanban board with demo data
   - 5 columns: Backlog, Discovery, In Progress, Review, Done
   - Demo cards with titles and descriptions
3. Test API endpoint: http://localhost:8000/api/test → JSON response
4. Test Kanban interactivity:
   - Drag and drop cards between columns
   - Add new card (should appear in column)
   - Delete card (should be removed)
   - Edit column title (should update)

### Next Steps

- Part 4: Add authentication (login/logout with "user"/"password")
- Part 5: Database schema finalization
- Part 6: Backend CRUD operations
