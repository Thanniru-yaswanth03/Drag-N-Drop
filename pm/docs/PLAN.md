# Project Implementation Plan & Roadmap

## Part 1: Plan

Enrich documentation, establish component architecture guidelines, and detail the complete implementation roadmap with checklists, test requirements, and success criteria for all project phases.

- [x] Analyze repository codebase, existing frontend components, and dependencies.
- [x] Create `frontend/AGENTS.md` describing frontend technology stack, component hierarchy, state management, and test suite.
- [x] Enrich `docs/PLAN.md` with granular substeps, test requirements, and success criteria for Parts 1 through 10.
- [x] Obtain user approval on the implementation plan.

### Tests & Verification
- Verify `frontend/AGENTS.md` exists and accurately documents `frontend/src` components and tests.
- Verify `docs/PLAN.md` contains complete checklists and criteria without emojis.

### Success Criteria
- User review and approval obtained for Part 1 plan.
- All documentation files are updated and aligned with project requirements.

---

## Part 2: Scaffolding

Set up the Docker infrastructure, Python FastAPI backend in `backend/`, and start/stop scripts in `scripts/`.

- [x] Create Python environment requirements (`pyproject.toml` / `requirements.txt`) including FastAPI, Uvicorn, Pydantic, and HTTPX.
- [x] Implement `backend/main.py` with FastAPI initialization, health check route `GET /api/health`, and example static HTML endpoint at `/`.
- [x] Create root `Dockerfile` using `uv` package manager for Python dependency installation and container execution.
- [x] Create start and stop scripts in `scripts/` (`start.sh`, `stop.sh`, `start.bat`, `stop.bat`, `start.ps1`, `stop.ps1`) supporting Mac, PC, and Linux.
- [x] Update `backend/AGENTS.md` and `scripts/AGENTS.md` with usage instructions.

### Tests & Verification
- Unit tests for `GET /api/health` and static root endpoints using `httpx` and `TestClient`.
- Execution test for `scripts/start` and `scripts/stop` scripts.

### Success Criteria
- Start script builds and launches Docker container locally.
- Accessing `http://localhost:8000/api/health` returns HTTP status 200.
- Accessing `http://localhost:8000/` serves example static HTML.
- Stop script cleanly halts container execution.

---

## Part 3: Add in Frontend

Build the Next.js frontend as a static export and serve it directly through the FastAPI backend container.

- [x] Configure `frontend/next.config.ts` for static export (`output: 'export'`).
- [x] Execute `npm run build` in `frontend/` to generate static `out/` directory.
- [x] Update `backend/main.py` to mount static directory and serve `index.html` at root `/`.
- [x] Update `Dockerfile` to multi-stage build: build Next.js static site, then copy into Python FastAPI runtime image.
- [x] Execute frontend unit and E2E test suite inside build environment.

### Tests & Verification
- Run `npm run test:all` in `frontend/`.
- Test static site serving from FastAPI endpoint.

### Success Criteria
- Docker container serves the full single-board Kanban studio at `http://localhost:8000/`.
- Drag-and-drop, column renaming, card creation, and deletion function in browser.
- All frontend Vitest and Playwright tests pass cleanly.

---

## Part 4: Add in a Fake User Sign-In Experience

Implement client-side and backend-assisted authentication requiring dummy credentials ("user", "password") to access the board.

- [x] Create Login view component in `frontend/src/components/LoginForm.tsx`.
- [x] Implement auth state check on root page: redirect unauthenticated users to Login view.
- [x] Validate hardcoded credentials (`user` / `password`).
- [x] Store session token/flag in browser storage or cookies.
- [x] Add Logout action button to header in `KanbanBoard.tsx`.
- [x] Add `/api/auth/login` and `/api/auth/logout` endpoints in FastAPI backend.

### Tests & Verification
- Frontend unit tests for login form validation and error handling.
- Playwright E2E test for login gate: verify unauthenticated access shows login screen, invalid credentials show error, valid credentials display board, and logout resets session.

### Success Criteria
- Visiting `/` without active session displays login form.
- Submitting `user` / `password` unlocks Kanban board.
- Clicking Logout returns user to login form.

---

## Part 5: Database Modeling

Design a database schema for Kanban boards and store schema definition in `docs/`.

- [x] Define database schema for users, boards, columns, and cards.
- [x] Create JSON schema specification in `docs/schema.json`.
- [x] Create `docs/DATABASE.md` explaining tables, relationships, and multi-user support model.
- [x] Obtain user sign-off on database design.

### Tests & Verification
- Validate sample board payloads against `docs/schema.json`.

### Success Criteria
- Complete JSON schema and entity-relationship model documented in `docs/`.
- Schema supports future multi-user and multi-board extensions while serving single-board MVP.
- User sign-off obtained on database specification.

---

## Part 6: Backend Database Integration & API Routes

Implement SQLite storage and CRUD API endpoints in FastAPI.

- [x] Set up SQLite connection manager in `backend/database.py` with auto-creation of database file if non-existent.
- [x] Implement Pydantic data models matching database schema.
- [x] Create API routes:
  - `GET /api/board`: Fetch user board state (seed default board if new user).
  - `PUT /api/board`: Update board state.
  - `POST /api/cards`: Add new card.
  - `PUT /api/cards/{id}`: Edit card details.
  - `DELETE /api/cards/{id}`: Remove card.
  - `PUT /api/columns`: Update column order or title.
- [x] Write backend unit tests using `pytest` and `httpx.AsyncClient`.

### Tests & Verification
- Execute `pytest` suite for backend DB operations and API endpoints.

### Success Criteria
- SQLite file auto-creates if missing on backend startup.
- All CRUD API routes function correctly and return standard HTTP status codes.
- Backend unit tests pass with 100% coverage on core endpoints.

---

## Part 7: Frontend + Backend Integration

Connect Next.js frontend state to FastAPI REST endpoints for full data persistence.

- [x] Implement API client service in `frontend/src/lib/api.ts`.
- [x] Replace static initial React state with initial fetch from `GET /api/board`.
- [x] Sync card drag-and-drop moves, column renames, card creation, and deletions with backend endpoints.
- [x] Add visual loading and saving indicators to header.
- [x] Run full end-to-end integration tests.

### Tests & Verification
- Run Vitest component tests with mocked API calls.
- Run Playwright E2E tests verifying board updates persist after page reloads.

### Success Criteria
- Kanban board state persists across browser page reloads and server restarts.
- UI gracefully handles network loading and error states.
- All Playwright E2E tests pass cleanly.

---

## Part 8: AI Connectivity

Integrate OpenRouter API client into backend and verify basic connection.

- [x] Add `OPENROUTER_API_KEY` handling in `backend/config.py` reading from root `.env`.
- [x] Create OpenRouter client service in `backend/ai.py` targeting model `openai/gpt-oss-120b`.
- [x] Implement test endpoint `POST /api/ai/test` executing a simple "2+2" prompt.
- [x] Write backend unit tests verifying OpenRouter request formatting and response parsing.

### Tests & Verification
- Execute `pytest` test for `POST /api/ai/test` endpoint.

### Success Criteria
- Endpoint `POST /api/ai/test` successfully connects to OpenRouter and returns valid response text.
- API key missing or network failure produces descriptive 500 error code.

---

## Part 9: AI Kanban Tooling & Structured Outputs

Extend AI service to accept user prompt + current Kanban JSON and return structured responses for board modifications.

- [x] Define Pydantic schema for AI Structured Output:
  - `reply`: Text response message for user.
  - `board_update`: Optional updated board state or array of card mutation commands (create/edit/move/delete).
- [x] Implement `POST /api/ai/chat` endpoint taking conversation history, prompt, and current board JSON.
- [x] Add system instructions enforcing board constraint preservation.
- [x] Validate AI structured output payload and execute database mutations when board updates are present.
- [x] Write unit tests for AI schema validation and database mutation execution.

### Tests & Verification
- `pytest` suite for structured output parsing, valid mutation handling, and invalid schema fallback.

### Success Criteria
- AI endpoint parses user intent and outputs structured JSON.
- When AI response requests board mutations, backend updates SQLite database correctly.
- Comprehensive unit tests pass.

---

## Part 10: AI Sidebar Chat UI

Add AI chat sidebar to frontend UI with real-time board update sync.

- [x] Build `AISidebar.tsx` component with slide-out drawer, chat history display, and input form.
- [x] Connect chat form to `POST /api/ai/chat` endpoint.
- [x] Add auto-refresh mechanism: when AI response includes board updates, update board state in React UI without requiring manual page reload.
- [x] Add action toast/badge highlighting cards modified or created by AI.
- [x] Execute complete test suite (frontend unit, backend unit, E2E).

### Tests & Verification
- Vitest component tests for `AISidebar.tsx`.
- Playwright E2E test verifying: user asks AI to add/move card -> AI responds -> board updates automatically.

### Success Criteria
- AI chat sidebar opens/closes smoothly with theme-compliant design.
- Chatting with AI permits natural language creation, editing, and moving of cards.
- Board UI refreshes automatically when AI modifies state.
- Entire project test suite passes 100%.