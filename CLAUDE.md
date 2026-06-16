# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanban project management MVP with a Next.js static frontend, FastAPI backend, and SQLite database. Authentication is hardcoded (username: `user`, password: `password`). An AI chat sidebar integrates with OpenAI to read and modify board state via natural language.

## Commands

### Backend
```bash
cd backend && python -m uvicorn main:app --reload   # dev server (port 8000)
cd backend && pytest tests/                          # all tests
cd backend && pytest tests/test_main.py::TestAPIEndpoints::test_api_test_endpoint  # single test
cd backend && pip install -r requirements.txt
```

### Frontend
```bash
cd frontend && npm run dev          # dev server (port 3000)
cd frontend && npm run build        # static export → frontend/out/
cd frontend && npm run test:unit    # Vitest unit tests
cd frontend && npm run test:e2e     # Playwright E2E tests
cd frontend && npm run lint
```

### Docker (recommended for full-stack)
```bash
docker compose up --build   # build and start
docker compose down
```
Or use `scripts/start.ps1` / `scripts/stop.ps1` on Windows.

### Environment
Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Optional backend vars: `OPENAI_MODEL` (default `gpt-4.1-2025-04-14`), `OPENAI_TIMEOUT_SECONDS`, `OPENAI_HISTORY_LIMIT`.

## Architecture

### Docker / Deployment
Multi-stage Dockerfile: Node builds the frontend static export, Python serves both the FastAPI API (`/api/*`) and the static frontend assets from `backend/public/out/`.

### Backend (`backend/`)
- `main.py` — all FastAPI routes and Pydantic request/response schemas in one file
- `models.py` — SQLAlchemy ORM: `User → Board → Column → Card`, plus `Conversation` for AI history
- `database.py` — SQLite engine with `PRAGMA foreign_keys=ON`
- `seed.py` — seeds default user/board/columns/cards on startup if empty
- Tests use an in-memory SQLite DB via fixtures in `tests/conftest.py`

Key API shape:
- `POST /api/login` → auth
- `GET /api/users/{user_id}/board` → full board state (columns + cards nested)
- `PATCH /api/cards/{card_id}/move` → move card between columns
- `POST /api/ai/chat` → send message + current board context, returns AI response and optional board mutations

### Frontend (`frontend/src/`)
- Next.js configured as a **static export** (`output: 'export'`). No server-side rendering — use only client components.
- `components/AuthProvider.tsx` — session stored in `localStorage`
- `components/KanbanBoard.tsx` — drag-and-drop with `@dnd-kit`
- `components/ChatSidebar.tsx` — AI chat interface
- `lib/api.ts` — typed API client for all backend calls
- `lib/kanban.ts` — `moveCard` helper for reordering card arrays locally

### Data Flow
Login → fetch board → display columns/cards → drag-drop calls `PATCH /move` → AI chat sends board snapshot, backend calls OpenAI, applies returned mutations, responds with updated board + message.

## Coding Guidelines (from AGENTS.md)
- Keep it simple — no over-engineering, always prefer the simpler solution
- Identify root cause before fixing; prove with evidence
- No emojis in code or docs
