# Project Management MVP - Detailed Implementation Plan

## Current Status

Last reviewed: 2026-06-16.

Parts 2–6 are implemented and verified. Parts 7–10 are substantially implemented in modified/untracked files (not yet committed). The Windows `scripts/start.bat` flow builds the frontend, builds the Docker image, starts the container, waits for `/api/test`, and serves the Kanban frontend at `http://localhost:8000/`.

### Current Design Decisions

- Use `docker compose` instead of the legacy `docker-compose` command in all start/stop scripts.
- Keep the app as one Docker service for the MVP: FastAPI serves the API under `/api/*` and serves the static Next.js export at `/`.
- Use `uv` in the Docker image to install Python dependencies from `backend/requirements.txt`.
- Use Next.js static export with `output: 'export'` and `distDir: 'out'`, producing `frontend/out`.
- FastAPI serves built frontend assets from `backend/public/out` inside the container.
- The host start scripts run `npm ci` only when the local Next.js binary is missing, then run `npm run build` so `frontend/out` exists for the compose volume mount.
- The Dockerfile also performs a frontend build in a Node builder stage and copies the exported `out` directory into the Python runtime image.
- `docker-compose.yml` intentionally omits the obsolete Compose `version` field.
- The Windows batch readiness check uses PowerShell `Invoke-WebRequest` with delayed `errorlevel` expansion so the script only reports ready after `/api/test` responds successfully.
- MVP authentication is client-side only for Part 4: `AuthProvider` stores the hardcoded `user` session in localStorage under `pm-auth-user`.
- Playwright uses port `3100` for the frontend dev server to avoid reusing unrelated local apps already running on port `3000`.

### Verified On 2026-05-11

- `npm run build` succeeds in `frontend/`.
- `docker compose build` succeeds.
- `scripts\start.bat` succeeds.
- `GET http://localhost:8000/api/test` returns status JSON.
- `GET http://localhost:8000/` returns the Kanban frontend HTML.
- Part 4 frontend unit tests pass.
- Part 4 Playwright E2E tests pass after installing the local Chromium runner.
- Part 5 schema design is documented in `docs/DATABASE_SCHEMA.md`, with runnable SQLite DDL in `docs/schema.sql`.
- Part 5 DDL was validated against an in-memory SQLite database.
- Part 6 backend SQLite persistence and board CRUD API routes are implemented.
- Part 6 backend tests pass, Python compile check passes, Ruff passes, and Docker runtime smoke tests pass.
- Local backend dependencies were installed from `backend/requirements.txt` so pytest and Ruff can run locally.
- Parts 7–10 are substantially implemented in modified/untracked files. Remaining gaps: 7.11 (per-operation loading spinners), 7.13 (backend logout call), 10.14 (input focus after send), and all Part 10 tests.

## Part 1: Planning & Architecture

### Overview

Define the complete architecture, API design, database schema, and create detailed implementation checklists for all subsequent parts.

### Substeps

- [ ] **1.1 API Design**: Define REST API endpoints for board operations (CRUD for cards, columns, users)
- [ ] **1.2 Database Schema**: Design normalized SQL schema for users, boards, columns, cards with migrations
- [ ] **1.3 Authentication Flow**: Document hardcoded login flow and session/token approach
- [ ] **1.4 AI Integration Design**: Define OpenAI API call structure, structured outputs format, conversation history
- [ ] **1.5 Error Handling Strategy**: Define error codes, logging approach, user-facing error messages
- [ ] **1.6 File Structure**: Finalize backend/frontend folder layout, script locations, environment config approach

### Tests

- None (planning phase)

### Success Criteria

- ✓ API endpoint spec document ready (RESTful, no auth token needed for MVP)
- ✓ Database schema diagram and SQL DDL created
- ✓ AI structured output schema documented (JSON format for card updates)
- ✓ All 10 parts have detailed substeps and success criteria defined
- ✓ User has reviewed and approved the plan

---

## Part 2: Docker & Backend Scaffolding

### Overview

Set up Docker infrastructure, initialize FastAPI backend, create start/stop scripts, and verify "hello world" functionality.

### Status

Implemented and verified through Docker startup.

### Substeps

- [x] **2.1 Dockerfile**: Create multi-stage Dockerfile using Python 3.12 runtime
- [x] **2.2 docker-compose.yml**: Set up container with volume mounts, port 8000, environment variables
- [x] **2.3 Backend structure**: Create `backend/` folder with `main.py`, `pyproject.toml`, `requirements.txt`
- [x] **2.4 FastAPI hello world**: Set up basic FastAPI app with `/` and `/api/test` endpoints returning JSON
- [x] **2.5 Start/Stop scripts**: Create `start.sh`, `start.bat`, `start.ps1` for Mac/Linux/Windows
- [x] **2.6 Stop scripts**: Create `stop.sh`, `stop.bat`, `stop.ps1` for graceful shutdown
- [x] **2.7 .env setup**: Create `.env` file template with OPENAI_API_KEY placeholder
- [x] **2.8 Verify running**: Test that `docker compose up` works and `/api/test` endpoint responds
- [x] **2.9 Static HTML**: Serve simple HTML at `/` confirming "hello world"

### Tests

**Unit Tests**

- [ ] Test FastAPI routes return correct JSON structure
- [ ] Test environment variable loading
- [x] Test Docker Compose can build image

**Integration Tests**

- [x] Full Docker build and container startup succeeds
- [x] HTTP GET `/api/test` returns 200 and expected JSON
- [x] HTTP GET `/` returns 200 and HTML content

**Manual Tests**

- [x] Run on Windows: `start.bat` works and server is accessible at `http://localhost:8000`
- [ ] Run on Windows: `start.ps1` works and server is accessible at `http://localhost:8000`
- [ ] Run on Mac/Linux: `start.sh` works and server is accessible
- [ ] Run `stop.sh` (or bat) cleanly shuts down container
- [ ] `.env` file can load `OPENAI_API_KEY` without error if present

### Success Criteria

- ✓ Docker image builds without errors
- ✓ `docker compose up` brings up FastAPI server on port 8000
- ✓ `/` serves simple hello world HTML
- ✓ `/api/test` endpoint returns valid JSON response
- ✓ Start/stop scripts work on all three platforms (Windows, Mac, Linux)
- ✓ All environment variables load correctly from `.env`
- ✓ Server can be gracefully shut down

---

## Part 3: Integrate Frontend Build

### Overview

Build the NextJS frontend and serve it statically from FastAPI at `/`. Verify the Kanban board demo displays.

### Status

Implemented and verified through `scripts\start.bat`.

### Substeps

- [x] **3.1 Frontend build config**: Ensure `next.config.ts` exports static HTML to `frontend/out`
- [x] **3.2 Build process**: Add npm build script that runs `next build`
- [x] **3.3 Serve static files**: Update FastAPI to serve Next.js static output from `backend/public/out` and HTML from `/`
- [x] **3.4 Docker integration**: Update Dockerfile to build frontend in first stage, copy output to FastAPI app
- [x] **3.5 CORS setup**: Configure CORS headers for local origins
- [x] **3.6 API prefix routing**: Ensure `/api/*` routes go to FastAPI, other routes serve frontend
- [x] **3.7 Test frontend loads**: Verify Kanban board displays at `http://localhost:8000`
- [x] **3.8 Update .gitignore**: Ignore build outputs, `node_modules`, `.next`, `__pycache__`
- [x] **3.9 Start script dependency handling**: Install frontend dependencies with `npm ci` when `node_modules/.bin/next` is missing
- [x] **3.10 Windows readiness check**: Use delayed `errorlevel` expansion so `start.bat` correctly detects the running service

### Tests

**Unit Tests**

- [x] Frontend build creates expected output in `frontend/out`
- [x] FastAPI static file serving configuration is correct

**Integration Tests**

- [x] Docker build includes both frontend and backend
- [x] Full container startup with frontend assets works
- [x] HTTP GET `/` returns Kanban board HTML
- [ ] Static assets (CSS, JS) load without 404 errors
- [ ] Kanban board is interactive (drag/drop works)

**Manual Tests**

- [x] Open `http://localhost:8000` in browser or request root HTML
- [ ] Kanban board displays with all 5 columns and demo cards
- [ ] Drag and drop cards between columns
- [ ] Add new card and it appears
- [ ] Delete card and it disappears
- [ ] Edit column title and change persists

### Success Criteria

- ✓ Frontend builds successfully as static files
- ✓ Frontend assets are served from FastAPI without 404 errors
- ✓ Kanban board displays at `http://localhost:8000/`
- ✓ All frontend interactivity works (drag/drop, add, delete, rename)
- ✓ Docker image includes both frontend build and backend code
- ✓ Single `docker compose up` brings everything up

---

## Part 4: Authentication (Hardcoded Login)

### Overview

Add a login page at `/` with hardcoded credentials ("user"/"password"). After login, show Kanban board. Add logout functionality.

### Status

Implemented and verified in frontend unit tests and Playwright E2E tests.

### Substeps

- [x] **4.1 Auth context**: Create React Context for user state (logged in / logged out)
- [x] **4.2 Login page**: Create new component `/login` with username/password form
- [x] **4.3 Session storage**: Store logged-in user state in localStorage (client-side, MVP only)
- [x] **4.4 Root page redirect**: Redirect to `/login` if not logged in
- [x] **4.5 Logout button**: Add logout button to Kanban board header
- [x] **4.6 Credentials check**: Add client-side validation for "user" / "password" (no backend for MVP)
- [x] **4.7 Session persistence**: Load user session from localStorage on page refresh
- [x] **4.8 Clear session**: Logout clears localStorage and redirects to `/login`
- [x] **4.9 Protect routes**: Ensure only logged-in users can access Kanban board

### Tests

**Unit Tests**

- [x] Auth context correctly toggles login state
- [x] localStorage.setItem/getItem called correctly on login
- [x] Credentials validation logic works

**Integration Tests**

- [x] Visiting `/` while logged out redirects to `/login`
- [x] Logging in with "user"/"password" redirects to `/`
- [x] Logging in with wrong credentials shows error message
- [x] Page refresh maintains logged-in state
- [x] Logout clears session and redirects to `/login`
- [x] Visiting `/` while logged in shows Kanban board directly

**E2E Tests (Playwright)**

- [x] Full login flow: visit -> enter credentials -> see Kanban
- [x] Logout flow: click logout -> see login page
- [x] Session persistence: login -> refresh page -> still logged in
- [x] Wrong credentials: attempt login with invalid password -> error appears

### Success Criteria

- ✓ Unauthenticated users are redirected from `/` to `/login`
- ✓ "user"/"password" credentials log in successfully
- ✓ Wrong credentials show clear error
- ✓ Logged-in users see Kanban board
- ✓ Session persists on page refresh
- ✓ Logout button present and functional
- ✓ All auth flows tested and passing

---

## Part 5: Database Schema Design

### Overview

Design a normalized SQL schema for multi-user support. Document database approach and get user sign-off before implementation.

### Status

Approved by user direction to proceed to Part 6.

### Design Documents

- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- [schema.sql](schema.sql)

### Schema

**Users Table**

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Boards Table**

```sql
CREATE TABLE boards (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL DEFAULT 'My Board',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Columns Table**

```sql
CREATE TABLE columns (
  id TEXT PRIMARY KEY,
  board_id TEXT NOT NULL,
  title TEXT NOT NULL,
  position INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
  UNIQUE (board_id, position)
);
```

**Cards Table**

```sql
CREATE TABLE cards (
  id TEXT PRIMARY KEY,
  column_id TEXT NOT NULL,
  title TEXT NOT NULL,
  details TEXT NOT NULL DEFAULT '',
  position INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE,
  UNIQUE (column_id, position)
);
```

**Conversation History Table** (for AI chat)

```sql
CREATE TABLE conversations (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  board_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  message TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
);
```

### Substeps

- [x] **5.1 Schema diagram**: Create visual ER diagram showing relationships
- [x] **5.2 Normalization review**: Ensure 3NF, no redundant data
- [x] **5.3 Indexing strategy**: Identify columns that need indexes (user_id, board_id, column_id)
- [x] **5.4 DDL generation**: Generate SQL DDL for all tables with constraints
- [x] **5.5 Migration approach**: Decide on migration tool/strategy (SQLAlchemy `create_all` or startup initializer for MVP; Alembic later)
- [x] **5.6 Document assumptions**: Record why each table/column exists, constraints reasoning
- [x] **5.7 User review**: Present schema to user for feedback

### Tests

- [x] Validate `docs/schema.sql` in an in-memory SQLite database

### Success Criteria

- ✓ Schema diagram created
- ✓ All tables properly normalized
- ✓ Foreign key constraints defined
- ✓ Unique constraints prevent duplicate data
- ✓ Cascade delete configured appropriately
- ✓ User has approved schema design
- ✓ DDL script can create all tables

---

## Part 6: Backend API - Database & CRUD Routes

### Overview

Implement SQLite database integration, create migrations, and build API routes for board CRUD operations.

### Status

Implemented and verified with backend tests and Docker runtime smoke tests.

### Substeps

- [x] **6.1 Database setup**: Create SQLAlchemy models matching schema from Part 5
- [x] **6.2 Database initialization**: Create `database.py` module with session management
- [x] **6.3 DB auto-creation**: Ensure database is created on startup if missing
- [x] **6.4 Migrations**: Use SQLAlchemy `create_all` startup initialization for the MVP
- [x] **6.5 Models**: Create SQLAlchemy ORM models for User, Board, Column, Card, Conversation
- [x] **6.6 User API**:
  - [x] `POST /api/users` - Create user
  - [x] `GET /api/users/{user_id}` - Get user by ID or username
- [x] **6.7 Board API**:
  - [x] `GET /api/users/{user_id}/board` - Get user's board with columns and cards
  - [x] `PUT /api/users/{user_id}/board` - Update board title
- [x] **6.8 Column API**:
  - [x] `PUT /api/boards/{board_id}/columns/{column_id}` - Rename column
  - [x] `GET /api/boards/{board_id}/columns` - List columns for board
- [x] **6.9 Card API**:
  - [x] `POST /api/columns/{column_id}/cards` - Create card
  - [x] `PUT /api/cards/{card_id}` - Update card (title, details)
  - [x] `DELETE /api/cards/{card_id}` - Delete card
  - [x] `PATCH /api/cards/{card_id}/move` - Move card to different column
- [x] **6.10 Response standardization**: Ensure all endpoints return consistent JSON structure
- [x] **6.11 Error handling**: Return appropriate HTTP status codes (400, 404)

### Tests

**Unit Tests**

- [x] Database models can be created and serialized to JSON
- [x] Cascade delete works correctly
- [x] Date fields are set correctly

**Integration Tests**

- [x] `POST /api/users` creates user and returns ID
- [x] `GET /api/users/{user_id}/board` returns full board structure
- [x] `POST /api/columns/{column_id}/cards` creates card with correct position
- [x] `PUT /api/cards/{card_id}` updates title/details
- [x] `DELETE /api/cards/{card_id}` removes card and updates column cardIds
- [x] `PATCH /api/cards/{card_id}/move` moves card between columns
- [x] `PUT /api/boards/{board_id}/columns/{column_id}` renames column
- [x] Moving card updates position/order correctly
- [x] Getting board after operations returns correct state
- [x] Non-existent resources return 404
- [x] Invalid data returns 400

**Database Tests**

- [x] SQLite database file is created if missing
- [x] Initial data or seed data loads correctly
- [x] Foreign key constraints prevent orphaned records
- [x] All CRUD operations persist correctly
- [x] Database can be deleted and recreated in tests

### Success Criteria

- ✓ SQLite database auto-creates on first run
- ✓ All API endpoints implemented and respond with 200/201 status
- ✓ Full board data retrieved in single request (columns + cards)
- ✓ Card creation/deletion updates column correctly
- ✓ Card movement between columns works
- ✓ Column renaming works
- ✓ Error cases return appropriate status codes
- ✓ All integration tests pass
- ✓ Database state persists across server restarts

---

## Part 7: Frontend + Backend Integration

### Overview

Update frontend to use backend API instead of in-memory state. Persist all operations to server.

### Substeps

- [x] **7.1 API client**: Create `lib/api.ts` with helper functions for backend calls
- [x] **7.2 Environment config**: Add `NEXT_PUBLIC_API_URL` env variable (default `http://localhost:8000`)
- [x] **7.3 Auth update**: Add POST `/api/login` endpoint to backend for authentication (hardcoded check)
- [x] **7.4 Auth refactor**: Update frontend auth context to call backend login instead of local validation
- [x] **7.5 Load board on mount**: Update KanbanBoard to fetch `/api/users/{userId}/board` on mount
- [x] **7.6 Add card sync**: Update addCard handler to POST to backend, then update state with response
- [x] **7.7 Delete card sync**: Update deleteCard handler to DELETE to backend first
- [x] **7.8 Move card sync**: Update moveCard handler to PATCH to backend with new column_id
- [x] **7.9 Rename column sync**: Update renameColumn handler to PUT to backend
- [x] **7.10 Error handling**: Display user-friendly error messages for failed API calls
- [ ] **7.11 Loading states**: Show loading spinners during async operations (board-level spinner only; no per-operation spinners)
- [x] **7.12 Optimistic updates**: Update UI immediately, rollback on error
- [ ] **7.13 Logout sync**: DELETE session on backend when user logs out (logout currently only clears localStorage)

### Tests

**Unit Tests**

- [ ] API client methods format requests correctly
- [ ] Error responses are handled properly
- [ ] Env variables are read correctly

**Integration Tests**

- [x] Login POST request with correct credentials succeeds
- [x] Login with wrong credentials fails
- [x] Board data loads from API on component mount
- [x] Adding card calls POST and updates state
- [x] Deleting card calls DELETE and removes from board
- [x] Moving card calls PATCH with correct column_id
- [x] Renaming column calls PUT and updates title
- [ ] Error message displays when API fails
- [ ] Loading spinner shows during API calls

**E2E Tests (Playwright)**

- [ ] Full flow: login → see board → add card → card appears → refresh → card still there
- [ ] Delete card → card disappears → refresh → still gone
- [ ] Move card between columns → refresh → position persists
- [ ] Rename column → refresh → new title shows
- [ ] Multiple users have separate boards (create 2 user sessions)

**API Contract Tests**

- [ ] Frontend correctly serializes requests to match backend API schema
- [ ] Frontend correctly deserializes responses
- [ ] All endpoints return expected fields

### Success Criteria

- ✓ Frontend successfully authenticates with backend
- ✓ Board data loads from backend on page load
- ✓ All card operations (add/edit/delete/move) persist to backend
- ✓ Column rename persists
- ✓ Page refresh shows latest state from backend
- ✓ Error messages display for failed operations
- ✓ Multiple users have separate, persistent boards
- ✓ All E2E tests pass
- ✓ No console errors

---

## Part 8: AI Connectivity - OpenAI Integration

### Overview

Set up OpenAI API connectivity, test with simple query, verify structured outputs work.

### Substeps

- [x] **8.1 OpenAI client**: Install `openai` Python package
- [x] **8.2 API key loading**: Load `OPENAI_API_KEY` from `.env` file
- [x] **8.3 Test endpoint**: Create `POST /api/ai/test` endpoint
- [x] **8.4 Simple query**: Test with "What is 2+2?" to verify basic connectivity
- [x] **8.5 Response parsing**: Parse OpenAI response and return JSON
- [x] **8.6 Error handling**: Handle API errors (rate limit, auth, network)
- [x] **8.7 Logging**: Log all AI requests/responses for debugging
- [x] **8.8 Timeout handling**: Set request timeout (30 seconds)
- [x] **8.9 Structured outputs**: Define JSON schema for AI to return structured responses

### Tests

**Unit Tests**

- [ ] OpenAI client initializes with correct API key
- [ ] Request formatting is correct for OpenAI API
- [ ] Response parsing extracts message correctly

**Integration Tests**

- [x] POST `/api/ai/test` with prompt returns JSON response
- [x] Response contains correct answer to "2+2=4"
- [x] Missing API key returns clear error message
- [x] Timeout after 30 seconds (use mock)
- [ ] Rate limit error handled gracefully

**Manual Tests**

- [ ] Run `/api/ai/test` endpoint manually, verify response
- [ ] Check `.env` has valid `OPENAI_API_KEY`
- [ ] Test with invalid key, verify error message

### Success Criteria

- ✓ OpenAI API key loads correctly from `.env`
- ✓ `/api/ai/test` endpoint responds with 200 status
- ✓ "2+2" test returns correct answer in JSON
- ✓ Error handling for missing/invalid key works
- ✓ Structured output schema defined and validated
- ✓ All tests pass
- ✓ No API credentials in source code

---

## Part 9: AI Awareness of Kanban State

### Overview

Extend AI to receive full Kanban board state with user query, return structured response with optional board updates.

### Substeps

- [x] **9.1 Structured output schema**: Define JSON schema for AI response:
  ```json
  {
    "message": "string",
    "boardUpdates": {
      "cards": [{ "id": "...", "action": "create|update|delete|move", ... }],
      "columns": [{ "id": "...", "title": "..." }]
    }
  }
  ```
- [x] **9.2 Board state serialization**: Function to convert Board ORM to JSON for AI context
- [x] **9.3 Conversation history table**: Store message history for context window
- [x] **9.4 System prompt**: Create detailed system prompt explaining Kanban format and expected responses
- [x] **9.5 Chat endpoint**: Create `POST /api/ai/chat` endpoint
  - [x] Accept `user_id`, `message`, `board_id`
  - [x] Load conversation history from DB
  - [x] Include full board state in request
  - [x] Call OpenAI with structured outputs
  - [x] Parse response and return JSON
  - [x] Store user message and AI response in history
- [x] **9.6 Board update handling**: Parse AI's suggested board updates, validate, but don't apply yet (UI decides)
- [x] **9.7 Error recovery**: Handle malformed AI responses gracefully

### Tests

**Unit Tests**

- [x] Board state serializes correctly to JSON
- [x] Conversation history loads in correct order
- [x] System prompt contains required instructions
- [x] Structured output parsing works for valid responses

**Integration Tests**

- [x] POST `/api/ai/chat` with simple question returns response
- [x] Response includes "message" field
- [x] Conversation history is saved to DB
- [x] Multiple chat turns maintain context
- [ ] Board updates in response match valid card/column operations
- [x] Invalid AI response (malformed JSON) returns error without crash
- [ ] Different users have separate conversation histories

**Manual Tests**

- [ ] Send "Add a task to prioritize API design" → AI suggests card creation
- [ ] Verify suggested card includes title and column
- [ ] Send follow-up "make it more urgent" → AI responds with context

### Success Criteria

- ✓ AI receives full board state with user message
- ✓ AI returns structured response with message + optional updates
- ✓ Conversation history persists across chats
- ✓ Multiple users have isolated conversations
- ✓ AI responses validate against schema
- ✓ All integration tests pass
- ✓ Malformed responses handled gracefully

---

## Part 10: AI Chat Sidebar & Board Updates

### Overview

Add beautiful AI chat sidebar to UI. Allow user to apply AI-suggested board updates. Implement real-time board refresh.

### Substeps

- [x] **10.1 Sidebar layout**: Add sidebar container to main layout (split view with board and chat)
- [x] **10.2 Chat component**: Create `ChatSidebar.tsx` component with message list and input
- [x] **10.3 Message styling**: Style chat messages (user vs assistant, timestamp, code blocks)
- [x] **10.4 Input form**: Add message input field with send button (Enter to send)
- [x] **10.5 Scroll behavior**: Auto-scroll to latest message
- [x] **10.6 Loading state**: Show loading indicator while waiting for AI response
- [x] **10.7 Error display**: Show error messages in chat if request fails
- [x] **10.8 Message history**: Load previous conversation on component mount
- [x] **10.9 Board updates preview**: Display suggested board changes in chat for user review
- [x] **10.10 Apply updates**: Add "Apply Changes" button to accept AI suggestions
- [x] **10.11 Reject updates**: Allow user to dismiss suggestions without applying
- [x] **10.12 Live sync**: When updates applied, refresh board state from backend
- [x] **10.13 Responsive design**: Sidebar collapses on mobile
- [ ] **10.14 Focus management**: Focus input field after sending message

### Tests

**Unit Tests**

- [ ] ChatSidebar component renders correctly
- [ ] Message formatting logic works
- [ ] Input field captures text correctly

**Integration Tests**

- [ ] Sending message calls `/api/ai/chat` endpoint
- [ ] AI response displays in chat
- [ ] "Apply Changes" button triggers board update API calls
- [ ] Board state refreshes after updates applied
- [ ] Conversation history loads on mount
- [ ] Dismissing suggestions doesn't call API
- [ ] Multiple sequential messages work correctly

**E2E Tests (Playwright)**

- [ ] Full user journey: open app → ask AI to create task → see suggestion → apply → board updates
- [ ] Chat history persists on page refresh
- [ ] Sidebar responsive on different screen sizes
- [ ] Error message displays if API fails
- [ ] Auto-scroll keeps latest message visible
- [ ] "Enter" key sends message

**Visual Tests**

- [ ] Sidebar uses color scheme correctly
- [ ] Chat layout matches design specs
- [ ] Responsive layout works on mobile/tablet

### Success Criteria

- ✓ Beautiful sidebar chat UI implemented
- ✓ User can chat with AI about board
- ✓ AI suggestions display for user review
- ✓ User can apply or dismiss suggestions
- ✓ Board updates when suggestions applied
- ✓ Conversation history persists
- ✓ All E2E tests pass
- ✓ Responsive design works on mobile/desktop
- ✓ No console errors

---

## Overall Success Metrics

- [ ] **Code Quality**: All code follows coding standards, no unnecessary defensive programming
- [ ] **Test Coverage**: 80%+ coverage on backend, all critical paths E2E tested on frontend
- [ ] **Performance**: Page load < 2s, AI response < 10s
- [ ] **Reliability**: No unhandled errors, graceful degradation on API failures
- [ ] **Documentation**: README updated, API docs clear, code comments where complex
- [ ] **Deployment**: Single `docker compose up` brings full stack up locally
- [ ] **Persistence**: User data persists across server restarts
- [ ] **Multi-user**: Multiple users can log in and see separate boards
- [ ] **AI Accuracy**: AI understands Kanban context and makes valid update suggestions
