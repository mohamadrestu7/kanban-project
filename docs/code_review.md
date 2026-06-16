# Code Review Report

Reviewed: 2026-06-16  
Scope: Full repository — backend (FastAPI/SQLite), frontend (Next.js/React), tests, config  
Reviewer: Claude Code (automated multi-agent review)

---

## Executive Summary

The MVP is functionally complete and well-structured for a single-user local app. The main risks are:
- **No server-side authentication** — any caller who knows a `user_id` can read or mutate that user's data
- **Weak password hashing** (SHA-256, no salt) in the seeded default user
- **Hardcoded credentials exposed in the UI** error message
- **TypeScript build errors suppressed** — type safety is not enforced at build time
- Several medium-priority correctness gaps in optimistic updates, error rollback, and async handling

Most critical and high items are known MVP shortcuts that must be resolved before any multi-user or internet-facing deployment.

---

## Critical

### C1 — No server-side auth on any protected route
**File:** `backend/main.py` — all CRUD and AI endpoints  
The `/api/login` endpoint returns a `userId` that is then used as a plain URL parameter on all subsequent requests. There is no token, session, or signature validation. Any caller who discovers or guesses a `user_id` can read and modify that user's entire board.  
**Action:** Implement JWT or signed session tokens. Add a `Depends(get_current_user)` guard to every route that is not `/api/login`, `/api/test`, or `POST /api/users`. Verify that the authenticated user owns the requested resource before proceeding.

### C2 — Password hashing uses SHA-256 without a salt
**File:** `backend/seed.py:71-72`, `backend/main.py` (login comparison)  
SHA-256 is a general-purpose hash, not a password hash. Without a salt, identical passwords produce identical digests, and the entire database is vulnerable to rainbow-table attacks.  
**Action:** Replace with `bcrypt` or `argon2`. Add `passlib[bcrypt]` to `requirements.txt`. Update `seed.py` and the login comparison in `main.py`.

### C3 — Hardcoded credentials shown in UI error message
**File:** `frontend/src/components/LoginForm.tsx:23`  
On failed login, the error message reads `"Use username user and password password."` This ships a working credential hint directly to the browser.  
**Action:** Change to a generic message such as `"Invalid username or password."` Remove any credential hints from client-side code entirely.

---

## High

### H1 — CORS configured with wildcard methods and headers + credentials
**File:** `backend/main.py:116-128`  
`allow_methods=["*"]`, `allow_headers=["*"]`, and `allow_credentials=True` together allow any origin already in the list to make credentialed requests with any method and header. While origins are restricted to localhost for now, this pattern will be dangerous the moment an environment variable expands the origin list.  
**Action:** Replace `["*"]` with explicit lists: `allow_methods=["GET","POST","PUT","PATCH","DELETE"]`, `allow_headers=["Content-Type","Accept"]`. Load allowed origins from an environment variable rather than a hardcoded list.

### H2 — Overly broad OpenAI exception handling using string matching
**File:** `backend/main.py:275-298`, `main.py:433-483`  
Both `ai_test` and `ai_chat` catch all exceptions and try to classify them by matching substrings of the error message. This is fragile — OpenAI SDK exception messages vary across versions, and internal errors (database failures, memory errors) are silently mapped to 502.  
**Action:** Import and catch specific OpenAI SDK exception types (`AuthenticationError`, `RateLimitError`, `APITimeoutError`, etc.). Add a final `except Exception` that logs the full traceback and returns 500. Extract the mapping logic into a shared helper to avoid duplication (same code appears in two places).

### H3 — Optimistic rename not rolled back on failure
**File:** `frontend/src/components/KanbanBoard.tsx:124-140`  
Column rename applies the new title to local state immediately but does not store the original title. On API failure, the error banner appears but the title stays changed in the UI — the optimistic update is never reverted.  
**Action:** Capture `originalTitle` before updating state. In the `.catch()` handler, restore it before calling `loadBoard()` (or instead of calling `loadBoard()`).

### H4 — Missing error boundary around KanbanBoard
**File:** `frontend/src/components/ProtectedBoard.tsx`  
An unhandled render-time exception in `KanbanBoard` will crash the entire app with a blank screen. There is no error boundary to catch this.  
**Action:** Wrap `<KanbanBoard>` in a React `ErrorBoundary` component that renders a friendly fallback UI.

### H5 — `session.commit()` calls lack exception handling
**File:** `backend/main.py` — multiple endpoints (e.g. lines 468, 499, 542, 628, 658)  
SQLAlchemy `IntegrityError` (unique constraint, foreign key violation, check constraint) from a failed commit propagates as an unhandled 500. In some cases the exception message includes internal schema details.  
**Action:** Wrap each `session.commit()` in a `try/except IntegrityError` and raise `HTTPException(400, "Constraint violation")`. Add `from exc` to preserve the chain in logs.

---

## Medium

### M1 — TypeScript build errors suppressed
**File:** `frontend/next.config.ts:6-8`  
`typescript: { ignoreBuildErrors: true }` means type errors do not fail the build and can silently reach production.  
**Action:** Remove this option. Fix any type errors that surface.

### M2 — Race condition potential in drag-end handler
**File:** `frontend/src/components/KanbanBoard.tsx:82-116`  
The `handleDragEnd` function captures `nextColumns` in a closure passed to `queueMicrotask`. If a second drag completes before the microtask fires, the closure refers to an already-stale column snapshot. The API call then persists the wrong position.  
**Action:** Move the API call inside the `setBoard` callback (where the latest state is guaranteed), or use a ref to track the in-flight move and skip overlapping ones.

### M3 — `localStorage` accessed without SSR guard
**File:** `frontend/src/components/AuthProvider.tsx:58-62, 70-72, 100, 108`  
Direct `window.localStorage` access throws during server-side execution. Although the app is currently a static export, any future move to hybrid rendering would break auth silently.  
**Action:** Guard all `localStorage` access with `typeof window !== "undefined"`. A small `safeLocalStorage` utility makes this reusable.

### M4 — Mobile chat sidebar close button always hidden
**File:** `frontend/src/components/ChatSidebar.tsx:188-195`  
The "Close" button inside the sidebar header carries `hidden sm:hidden` (or equivalent), making it invisible on every viewport. On mobile the only way to close the modal is to tap the dim backdrop — there is no visible affordance.  
**Action:** Fix the Tailwind class to `hidden sm:block` (show on desktop) or add a visible close icon on mobile.

### M5 — `useEffect` suppresses exhaustive-deps lint rule
**File:** `frontend/src/components/KanbanBoard.tsx:65-68`  
`loadBoard` is called inside a `useEffect` whose dependency array is `[userId]` with an eslint-disable comment. If `loadBoard` is ever refactored to close over additional state, the stale-closure bug will be silent.  
**Action:** Wrap `loadBoard` in `useCallback([userId])` and add it to the effect dependency array instead of suppressing the lint rule.

### M6 — `ai_history` does not validate board ownership
**File:** `backend/main.py:374-390`  
The endpoint accepts `user_id` and `board_id` as independent query params and does not verify that the board belongs to the user. An authenticated user (once auth exists) could fetch another user's conversation history by supplying a known `board_id`.  
**Action:** After resolving C1, add an ownership check: `if board.user_id != user.id: raise HTTPException(403)`.

### M7 — Duplicate OpenAI error-handling logic
**File:** `backend/main.py:275-298` and `main.py:433-483`  
The same exception-to-HTTP-status mapping is written twice (once in `ai_test`, once in `ai_chat`).  
**Action:** Extract into a single `_raise_openai_error(exc)` helper and call it from both endpoints. (Depends on H2 being fixed first so the helper uses typed exceptions.)

### M8 — Missing indexes on foreign key columns
**File:** `backend/models.py`  
`Column.board_id`, `Card.column_id`, and `Conversation.user_id`/`board_id` are foreign keys without explicit `index=True`. SQLite does not automatically index foreign keys, so joins and filtered queries on these columns do a full-table scan.  
**Action:** Add `index=True` to each `mapped_column` that carries a foreign key.

### M9 — Inconsistent API response shapes
**File:** `backend/main.py` throughout  
Some endpoints return `{"status": "ok", ...}` (lines 237, 283, 629), others return the resource directly (lines 510, 514), and create endpoints return 201 with the resource. The frontend must handle multiple shapes.  
**Action:** Agree on one convention (e.g., create → 201 + resource; update/delete → 200 + resource; errors → `{"detail": "..."}`) and apply it uniformly.

### M10 — No rate limiting on AI endpoints
**File:** `backend/main.py:267, 393`  
`/api/ai/test` and `/api/ai/chat` are unbounded — any caller can trigger unlimited OpenAI API calls, running up cost and potentially hitting rate limits.  
**Action:** Add per-user or per-IP rate limiting using `slowapi` or a middleware guard. Log rate-limit events.

### M11 — AI board-update references not validated server-side
**File:** `backend/main.py` around line 448`  
The AI response may reference card IDs or column IDs that do not exist. These are returned to the frontend as-is; when the frontend tries to apply them it gets a 404. There is no server-side cross-check.  
**Action:** After parsing the AI response, verify that any non-null `id` fields in `boardUpdates.cards` and `boardUpdates.columns` correspond to real rows for this board. Strip or flag invalid references before returning.

---

## Low

### L1 — `Date.now()` used as message ID in chat
**File:** `frontend/src/components/ChatSidebar.tsx:104, 119`  
Two messages sent within the same millisecond receive the same local ID, causing React key collisions.  
**Action:** Replace with `crypto.randomUUID()`.

### L2 — No loading/disabled state during card operations in the form
**File:** `frontend/src/components/KanbanBoard.tsx` / `NewCardForm`  
The "Add card" submit button is not disabled while the `createCard` API call is in-flight, allowing duplicate submissions.  
**Action:** Thread an `isSubmitting` prop through to `NewCardForm` and disable the button while the call is pending.

### L3 — No visible logout redirect
**File:** `frontend/src/components/KanbanBoard.tsx:231-239`  
Clicking logout calls `onLogout()` which clears `localStorage`. The board remains visible for a moment until the auth check re-runs and redirects. The flicker is jarring.  
**Action:** Call `router.replace("/login")` immediately after `onLogout()` so the redirect is instant.

### L4 — Focus not restored to chat input after send
**File:** `frontend/src/components/ChatSidebar.tsx`  
After a message is submitted, `input` is cleared but the field loses focus. Users must click back into the field to send another message.  
**Action:** Hold a `ref` on the input and call `.focus()` inside the `finally` block of `sendMessage` (PLAN.md item 10.14).

### L5 — Delete card button lacks `focus-visible` style
**File:** `frontend/src/components/KanbanCard.tsx:42-49`  
The delete button has a `:hover` state but no `:focus-visible` outline, making keyboard navigation blind.  
**Action:** Add `focus-visible:ring-2 focus-visible:ring-[var(--primary-blue)]` to the button className.

### L6 — `Conversation.role` validated only at the database level
**File:** `backend/models.py:97`, `backend/main.py`  
The `CHECK (role IN ('user','assistant'))` constraint lives in SQLite only. There is no Pydantic `Literal` or `Enum` field on the request/response models, so invalid values reach the DB layer before being rejected.  
**Action:** Add `role: Literal["user", "assistant"]` to the relevant Pydantic model.

### L7 — Default password field on `UserCreate` is confusing
**File:** `backend/main.py:31-32`  
`UserCreate` defaults `password` to `"password"` — a silent footgun if the field is accidentally omitted.  
**Action:** Remove the default. Make `password` a required field with `Field(min_length=8)`.

### L8 — `selectinload` missing on columns endpoint
**File:** `backend/main.py:556-559`  
`GET /api/boards/{board_id}/columns` queries columns without eager-loading their cards. If `serialize_column` (line 194) is ever called on that result, it triggers a lazy query per column.  
**Action:** Add `.options(selectinload(Column.cards))` to the query.

### L9 — Test client in `test_main.py` does not use isolated DB
**File:** `backend/tests/test_main.py:15-17`  
Unlike the conftest fixtures, `test_main.py` creates its own `TestClient(app)` without overriding the database session. Tests depend on seeded production data and are not isolated.  
**Action:** Refactor to use the `client` fixture from `conftest.py`.

### L10 — No tests for authentication or cross-user access
**File:** `backend/tests/`  
There are no tests verifying that one user cannot read or modify another user's board, columns, or cards. Once C1 is fixed, these tests are essential regression guards.  
**Action:** Add parameterised tests for 403/404 responses when `user_id` does not match the authenticated user.

---

## Actions Summary

| ID | Severity | Area | Action |
|----|----------|------|--------|
| C1 | Critical | Backend security | Add JWT auth + per-route ownership checks |
| C2 | Critical | Backend security | Replace SHA-256 with bcrypt (add passlib) |
| C3 | Critical | Frontend security | Remove credential hint from LoginForm error |
| H1 | High | Backend security | Tighten CORS — explicit methods/headers, env-var origins |
| H2 | High | Backend error handling | Catch typed OpenAI exceptions, not string-matched catch-all |
| H3 | High | Frontend correctness | Roll back column rename on API failure |
| H4 | High | Frontend resilience | Add React ErrorBoundary around KanbanBoard |
| H5 | High | Backend error handling | Wrap `session.commit()` in `IntegrityError` handler |
| M1 | Medium | Frontend quality | Remove `ignoreBuildErrors: true` from next.config.ts |
| M2 | Medium | Frontend correctness | Fix stale-closure race in drag-end handler |
| M3 | Medium | Frontend correctness | Guard `localStorage` access with `typeof window` check |
| M4 | Medium | Frontend UX | Fix always-hidden mobile chat close button |
| M5 | Medium | Frontend correctness | Replace eslint-disable with `useCallback` on `loadBoard` |
| M6 | Medium | Backend security | Validate board ownership in `ai_history` endpoint |
| M7 | Medium | Backend quality | Extract shared OpenAI error handler (after H2) |
| M8 | Medium | Backend performance | Add `index=True` to all foreign key columns in models |
| M9 | Medium | Backend API | Standardise response shapes across all endpoints |
| M10 | Medium | Backend security | Add rate limiting to `/api/ai/test` and `/api/ai/chat` |
| M11 | Medium | Backend correctness | Validate AI board-update references exist before returning |
| L1 | Low | Frontend quality | Replace `Date.now()` IDs with `crypto.randomUUID()` |
| L2 | Low | Frontend UX | Disable add-card submit button while in-flight |
| L3 | Low | Frontend UX | Call `router.replace("/login")` immediately on logout |
| L4 | Low | Frontend UX | Focus chat input after send (PLAN.md 10.14) |
| L5 | Low | Frontend a11y | Add `focus-visible` ring to card delete button |
| L6 | Low | Backend quality | Add `Literal["user","assistant"]` to Pydantic role field |
| L7 | Low | Backend quality | Remove default `"password"` from `UserCreate.password` |
| L8 | Low | Backend performance | Add `selectinload(Column.cards)` to columns endpoint query |
| L9 | Low | Backend tests | Refactor `test_main.py` to use shared `client` fixture |
| L10 | Low | Backend tests | Add cross-user access tests (after C1 is resolved) |
