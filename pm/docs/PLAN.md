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
# Project Implementation Plan & Roadmap

## Part 11: Enhanced Task Management

Expand the existing card model and UI so each Kanban card supports richer task information while preserving existing CRUD and drag-and-drop behavior.

* [x] Extend the card/database schema with:

  * Description
  * Priority
  * Due date
  * Tags
  * Assignee/user reference
  * Created timestamp
  * Updated timestamp
* [x] Update `docs/schema.json` with the new card fields.
* [x] Update `docs/DATABASE.md` to document the extended card model.
* [x] Update Pydantic models and SQLite schema/migrations.
* [x] Extend existing card API routes to support the new fields.
* [x] Create or enhance a card details/edit modal.
* [x] Allow users to view and edit task description.
* [x] Add priority selection with Low, Medium, and High values.
* [x] Add optional due date.
* [x] Add tag creation/removal.
* [x] Display relevant task metadata directly on cards without overcrowding the board.
* [x] Preserve existing drag-and-drop behavior.

### Tests & Verification

* Unit tests for card creation and editing with all new fields.
* Backend tests validating new fields and invalid values.
* Frontend tests for the task details modal.
* Playwright E2E tests for creating and editing a detailed task.
* Verify existing card CRUD and drag-and-drop tests continue to pass.

### Success Criteria

* Users can create and edit detailed tasks.
* Task metadata persists in SQLite.
* Task details survive page refreshes.
* Existing AI card operations continue working.
* Existing tests remain passing.

---

## Part 12: Search, Filtering & Sorting

Add task discovery tools so users can efficiently navigate larger boards.

* [x] Add global task search input.
* [x] Search by task title and description.
* [x] Add priority filtering.
* [x] Add status/column filtering.
* [x] Add tag filtering.
* [x] Add due-date filtering.
* [x] Add sorting by:

  * Created date
  * Updated date
  * Due date
  * Priority
* [x] Add clear/reset filters action.
* [x] Display active filters clearly.
* [x] Ensure filtering does not mutate persisted board state.
* [x] Ensure search and filtering work correctly on mobile layouts.

### Tests & Verification

* Unit tests for filtering and sorting utilities.
* Component tests for search and filter controls.
* E2E tests combining multiple filters.
* Verify filtering does not alter database records.

### Success Criteria

* Users can quickly find tasks on large boards.
* Search and filters respond without unnecessary API requests.
* Clearing filters restores the complete board.
* Existing board functionality remains unaffected.

---

## Part 13: Multiple Projects & Boards

Extend the single-board MVP into a multi-project workspace while preserving backward compatibility with the existing board.

* [x] Update database schema to support multiple projects/boards per user.
* [x] Add project entity and relationships to users and boards.
* [x] Create API routes for:

  * `GET /api/projects`
  * `POST /api/projects`
  * `PUT /api/projects/{id}`
  * `DELETE /api/projects/{id}`
* [x] Associate cards and columns with the appropriate project/board.
* [x] Create project switcher UI.
* [x] Add create-project dialog.
* [x] Add rename-project functionality.
* [x] Add delete-project functionality with confirmation.
* [x] Preserve the existing default board as the initial project for existing users.
* [x] Prevent users from accessing another user's projects.

### Tests & Verification

* Backend tests for project CRUD.
* Authorization tests ensuring users cannot access another user's projects.
* Frontend tests for project switching.
* Playwright E2E test creating two projects with independent boards.

### Success Criteria

* One user can have multiple independent projects.
* Each project has its own columns and cards.
* Switching projects loads the correct board.
* Existing users do not lose their current board.
* Project data remains isolated between users.

---

## Part 14: Activity History

Add an activity/audit system that records important project and task changes.

* [x] Create activity/history database model.
* [x] Record events for:

  * Card creation
  * Card editing
  * Card deletion
  * Card movement
  * Column creation/rename/reorder
  * Project creation
  * Project updates
* [x] Store actor/user information.
* [x] Store timestamp.
* [x] Store relevant before/after values where appropriate.
* [x] Create `GET /api/projects/{id}/activity`.
* [x] Build activity history UI.
* [x] Display activity in chronological order.
* [x] Add useful human-readable activity messages.
* [x] Prevent normal users from modifying activity history.

### Tests & Verification

* Backend tests for activity creation.
* Tests verifying activity is generated for card mutations.
* Tests verifying activity belongs to the correct project.
* E2E test performing several actions and verifying activity history.

### Success Criteria

* Important project changes are auditable.
* Users can understand what changed and when.
* Activity records cannot be manipulated through normal task APIs.

---

## Part 15: Improved Authentication & Authorization

Replace the existing fake user authentication with a proper multi-user authentication system while preserving the existing login flow during development where necessary.

* [x] Replace hardcoded `user/password` authentication with database-backed users.
* [x] Create user model.
* [x] Store passwords securely using password hashing.
* [x] Implement registration endpoint.
* [x] Implement login endpoint.
* [x] Implement logout endpoint.
* [x] Implement authenticated session/token mechanism.
* [x] Add current-user endpoint such as `GET /api/auth/me`.
* [x] Protect board/project/card APIs.
* [x] Associate all persistent data with authenticated user IDs.
* [x] Add frontend registration UI.
* [x] Add frontend login validation.
* [x] Add session expiration handling.
* [x] Ensure unauthenticated users cannot access protected data.

### Tests & Verification

* Authentication unit tests.
* Password hashing tests.
* Invalid login tests.
* Session expiration tests.
* Authorization tests.
* Cross-user data isolation tests.
* Playwright E2E registration/login/logout flow.

### Success Criteria

* Multiple users can create independent accounts.
* Passwords are never stored in plain text.
* Users can only access their own projects and data.
* Authentication survives page refreshes.
* Unauthorized API requests are rejected.

---

## Part 16: Responsive Mobile Experience

Improve the application's mobile experience instead of simply shrinking the desktop UI.

* [x] Audit every major frontend component at mobile widths.
* [x] Improve Kanban column layout for small screens.
* [x] Improve touch interaction for drag-and-drop.
* [x] Optimize card details modal for mobile.
* [x] Optimize AI sidebar for mobile.
* [x] Improve project navigation on small screens.
* [x] Improve header controls and prevent overflow.
* [x] Ensure buttons and interactive elements have appropriate touch targets.
* [x] Add responsive empty states.
* [x] Test common mobile viewport sizes.
* [x] Verify no horizontal overflow exists.

### Tests & Verification

* Playwright responsive tests.
* Test mobile navigation.
* Test mobile card creation/editing.
* Test mobile drag-and-drop.
* Test AI sidebar on mobile.
* Test all major screens at desktop and mobile widths.

### Success Criteria

* Application is fully usable on mobile.
* No major horizontal overflow exists.
* Core Kanban interactions remain usable with touch.
* Existing desktop experience remains intact.

---

## Part 17: Undo, Redo & Optimistic Updates

Improve interaction reliability and perceived performance.

* [x] Implement undo support for appropriate board mutations.
* [x] Implement redo support where technically appropriate.
* [x] Add keyboard shortcuts for undo/redo.
* [x] Implement optimistic UI updates for fast interactions where safe.
* [x] Roll back optimistic changes when backend requests fail.
* [x] Display meaningful error feedback after failed mutations.
* [x] Prevent duplicate mutation requests.
* [x] Handle rapid drag-and-drop operations safely.
* [x] Ensure database remains the final source of truth.

### Tests & Verification

* Unit tests for undo/redo state handling.
* Tests for optimistic update rollback.
* Tests for failed API requests.
* E2E tests for moving and undoing task changes.
* Verify no data corruption occurs after repeated rapid actions.

### Success Criteria

* Common interactions feel immediate.
* Failed backend operations do not leave the UI in an incorrect state.
* Users can undo accidental changes.
* Database and frontend state remain consistent.

---

## Part 18: Team Collaboration & Permissions

Introduce project-level collaboration and role-based access control.

* [x] Create project membership model.
* [x] Support project roles:

  * Owner
  * Admin
  * Member
  * Viewer
* [x] Implement invitation workflow.
* [x] Add project member management UI.
* [x] Implement permission checks on backend APIs.
* [x] Prevent viewers from modifying project data.
* [x] Restrict project administration to Owner/Admin.
* [x] Allow owners/admins to remove members.
* [x] Display project members and roles.
* [x] Associate card assignees with project members.

### Tests & Verification

* Backend permission unit tests.
* Authorization tests for every project role.
* Cross-user security tests.
* E2E invitation/member-management tests.
* Verify viewers cannot mutate board state.

### Success Criteria

* Multiple users can collaborate on one project.
* Backend authorization is enforced independently of frontend controls.
* Each role has clearly defined permissions.
* Unauthorized mutations are rejected.

---

## Part 19: Real-Time Collaboration

Add real-time synchronization so multiple users viewing the same project receive updates without manually refreshing.

* [x] Evaluate WebSocket implementation suitable for the existing FastAPI backend.
* [x] Implement project-specific WebSocket channels.
* [x] Broadcast relevant board mutations.
* [x] Broadcast:

  * Card creation
  * Card editing
  * Card movement
  * Card deletion
  * Column changes
* [x] Update React state when remote mutations arrive.
* [x] Avoid applying duplicate local mutations.
* [x] Handle reconnects gracefully.
* [x] Display connection status.
* [x] Handle simultaneous edits predictably.
* [x] Ensure users can only subscribe to projects they are authorized to access.

### Tests & Verification

* Backend WebSocket tests.
* Authorization tests for WebSocket connections.
* Multi-client integration tests.
* E2E test with two browser contexts editing the same board.
* Test reconnect behavior.

### Success Criteria

* Changes made by one user appear on another user's screen without refresh.
* Unauthorized users cannot subscribe to private projects.
* Reconnecting clients eventually reach a consistent board state.

---

## Part 20: Notifications & Due-Date Management

Introduce useful notifications based on task deadlines and project activity.

* [x] Add notification database model.
* [x] Generate notifications for relevant events.
* [x] Add due-date reminders.
* [x] Add task assignment notifications.
* [x] Add project invitation notifications.
* [x] Add notification center UI.
* [x] Support read/unread notification states.
* [x] Add mark-as-read functionality.
* [x] Add notification count indicator.
* [x] Avoid generating duplicate notifications.
* [x] Design a backend mechanism for scheduled due-date checks.

### Tests & Verification

* Backend notification tests.
* Due-date reminder tests.
* Read/unread state tests.
* E2E notification interaction tests.
* Verify duplicate notifications are not generated.

### Success Criteria

* Users receive relevant notifications.
* Notifications persist correctly.
* Read/unread state is preserved.
* Due-date reminders are generated reliably.

---

## Part 21: AI Project Intelligence

Expand the existing AI functionality beyond direct card mutations.

* [x] Allow AI to summarize the current project.
* [x] Allow AI to identify overdue tasks.
* [x] Allow AI to identify high-priority unfinished tasks.
* [x] Allow AI to analyze workload distribution.
* [x] Allow AI to suggest task priorities.
* [x] Allow AI to suggest project organization improvements.
* [x] Allow AI to generate project progress summaries.
* [x] Add structured AI commands for supported analytical operations.
* [x] Ensure AI cannot bypass backend authorization.
* [x] Keep all AI-generated database mutations validated by backend schemas.
* [x] Display AI-generated changes clearly to the user.

### Tests & Verification

* Unit tests for AI structured responses.
* Tests for invalid AI output.
* Tests ensuring AI cannot modify unauthorized projects.
* Tests for project-summary generation.
* E2E tests for AI project analysis.
* Verify AI mutations continue to use existing validation.

### Success Criteria

* AI provides useful project-specific analysis.
* AI can understand the current board state.
* AI cannot perform unauthorized mutations.
* AI responses remain grounded in actual project data.

---

## Part 22: Production Hardening & Security

Prepare the application for real-world deployment rather than treating development defaults as production architecture.

* [x] Remove development-only hardcoded credentials.
* [x] Review all environment variables and secrets.
* [x] Ensure `.env` files containing secrets are excluded from Git.
* [x] Validate all backend request payloads.
* [x] Add appropriate CORS configuration.
* [x] Add rate limiting where appropriate.
* [x] Add authentication failure protections.
* [x] Review SQL query handling.
* [x] Review authorization on every protected endpoint.
* [x] Review file and path handling.
* [x] Add security-focused logging without exposing secrets.
* [x] Review AI API key handling.
* [x] Review error responses for information leakage.
* [x] Add production configuration separate from development configuration.

### Tests & Verification

* Run dependency/security audits.
* Test unauthorized API access.
* Test malformed request payloads.
* Test cross-user resource access.
* Verify secrets are not committed.
* Verify production configuration does not contain development credentials.

### Success Criteria

* No hardcoded production credentials remain.
* Protected resources enforce authorization.
* Secrets are handled through environment configuration.
* Backend validation rejects malformed or unauthorized requests.
* Security review findings are documented and resolved where practical.

---

## Part 23: Performance & Reliability

Optimize the application after functionality and security are stable.

* [x] Profile frontend rendering performance.
* [x] Identify unnecessary React re-renders.
* [x] Optimize large-board rendering.
* [x] Optimize API requests.
* [x] Prevent unnecessary board refetches.
* [x] Add appropriate database indexes.
* [x] Optimize frequently used SQLite queries.
* [x] Add pagination or lazy loading where appropriate for large activity/notification datasets.
* [x] Optimize AI request handling.
* [x] Add request timeouts.
* [x] Add appropriate retry behavior for transient failures.
* [x] Improve loading states.
* [x] Improve error recovery.

### Tests & Verification

* Measure baseline performance before optimization.
* Test large boards with many cards.
* Test repeated API operations.
* Test backend response times.
* Verify optimizations do not break existing behavior.

### Success Criteria

* Large boards remain responsive.
* API operations remain reliable under normal usage.
* No unnecessary network requests occur.
* Performance improvements are measurable rather than based on guesswork.

---

## Part 24: Final UX & Visual Polish

Perform a complete product-quality UI pass after all core functionality is stable.

* [x] Establish consistent spacing and typography.
* [x] Standardize buttons and interactive controls.
* [x] Improve loading states.
* [x] Improve empty states.
* [x] Improve error states.
* [x] Improve confirmation dialogs.
* [x] Improve toast notifications.
* [x] Improve hover/focus/active states.
* [x] Add accessible labels where necessary.
* [x] Review keyboard navigation.
* [x] Review color contrast.
* [x] Review dark/light theme consistency if supported.
* [x] Remove redundant UI elements.
* [x] Remove unused components and styles.
* [x] Ensure visual consistency across all pages.

### Tests & Verification

* Accessibility review.
* Keyboard navigation review.
* Desktop visual review.
* Mobile visual review.
* Cross-browser smoke testing.
* Run complete frontend and backend test suites.

### Success Criteria

* Application looks and behaves like a cohesive product.
* No major visual inconsistencies remain.
* Core workflows are intuitive.
* Accessibility issues discovered during review are addressed where practical.

---

## Part 25: Final Production Validation & Documentation

Perform a complete end-to-end validation of the application and prepare the project for portfolio and production presentation.

* [x] Run complete backend test suite.
* [x] Run complete frontend test suite.
* [x] Run complete Playwright E2E suite.
* [x] Build production frontend.
* [x] Build production Docker image.
* [x] Test production container locally.
* [x] Verify authentication.
* [x] Verify multi-user isolation.
* [x] Verify project CRUD.
* [x] Verify task CRUD.
* [x] Verify drag-and-drop persistence.
* [x] Verify AI task operations.
* [x] Verify AI project analysis.
* [x] Verify mobile functionality.
* [x] Verify collaboration if implemented.
* [x] Verify notifications if implemented.
* [x] Review application logs.
* [x] Update `README.md` with:

  * Project overview
  * Features
  * Architecture
  * Technology stack
  * Local setup
  * Environment variables
  * Database information
  * API overview
  * Testing instructions
  * Docker instructions
  * Deployment instructions
* [x] Add architecture diagram.
* [x] Add screenshots/GIFs where useful.
* [x] Document important engineering decisions.
* [x] Document known limitations.
* [x] Document future improvements.
* [x] Remove obsolete documentation and development artifacts.

### Tests & Verification

* Complete test suite must pass.
* Production build must succeed.
* Production Docker image must start successfully.
* All critical user workflows must be manually verified.
* No known critical security or data-integrity issues remain.

### Success Criteria

* Application is production-ready to the extent supported by the chosen infrastructure.
* Documentation is sufficient for another developer to clone, configure, run, test, and understand the project.
* Project demonstrates full-stack engineering capabilities rather than only frontend implementation.
* Existing functionality from Parts 1 through 24 remains intact.

## Part 26: Security Audit & Production Remediation

Perform an independent security, reliability, and production-readiness audit of the completed application based on the actual implementation rather than relying on existing documentation or previously marked checklist items.

This part exists to identify and remediate security and production issues that may remain after Parts 1 through 25.

Do not rewrite working architecture unnecessarily. Preserve existing functionality and make targeted changes supported by concrete findings.

### Security & Authentication Remediation

* [x] Audit the complete authentication flow from frontend login/registration through backend identity verification.
* [x] Remove all reliance on client-controlled `username` query parameters or request fields as proof of identity.
* [x] Ensure protected backend endpoints derive the authenticated user exclusively from a verified session/token.
* [x] Remove insecure default authenticated identities such as `username="user"`.
* [x] Replace deterministic token generation with cryptographically secure authentication credentials.
* [x] Ensure authentication credentials have appropriate expiration and invalidation behavior.
* [x] Implement real logout/session invalidation.
* [x] Review `GET /api/auth/me` so it derives identity from the authenticated session rather than a client-supplied username.
* [x] Remove development-only default credentials from production behavior.
* [x] Ensure test users/credentials are isolated from production configuration.
* [x] Review password hashing and ensure every password uses a unique cryptographically random salt.
* [x] Ensure passwords are never stored in `localStorage`, `sessionStorage`, cookies, logs, or API responses.
* [x] Remove any frontend persistence of plaintext passwords.
* [x] Ensure authentication state is cleared correctly during logout.

### Authorization & Multi-Tenant Isolation

* [x] Audit every protected API endpoint for authentication requirements.
* [x] Audit every protected API endpoint for authorization requirements.
* [x] Verify project ownership/membership on every project-scoped operation.
* [x] Verify card ownership/project membership on every card mutation.
* [x] Verify activity history belongs to the authenticated user's accessible project.
* [x] Verify notifications belong to the authenticated user.
* [x] Verify project member operations require appropriate project roles.
* [x] Verify viewers cannot perform mutations.
* [x] Verify Member/Admin/Owner permissions match the documented RBAC model.
* [x] Perform an IDOR audit against project IDs, card IDs, notification IDs, activity IDs, and membership IDs.
* [x] Attempt horizontal privilege escalation between two users.
* [x] Attempt vertical privilege escalation between project roles.
* [x] Ensure changing IDs or request parameters cannot bypass authorization.

### WebSocket Security

* [x] Require authenticated identity for WebSocket connections.
* [x] Verify project membership before allowing a WebSocket subscription.
* [x] Prevent clients from joining unauthorized project channels.
* [x] Ensure WebSocket messages cannot bypass REST/API authorization rules.
* [x] Validate incoming WebSocket payloads.
* [x] Handle malformed and oversized WebSocket messages safely.
* [x] Clean up disconnected clients reliably.
* [x] Prevent cross-project message leakage.
* [x] Verify reconnect behavior.
* [x] Verify multi-user synchronization remains consistent.

### AI Security & Reliability

* [x] Require authentication for AI endpoints.
* [x] Enforce project-level authorization before AI operations.
* [x] Validate every AI-generated structured response before database mutation.
* [x] Validate card IDs against the current project.
* [x] Validate column IDs against the current project.
* [x] Validate mutation types against an explicit allowlist.
* [x] Validate all generated fields using backend schemas.
* [x] Reject malformed, oversized, or structurally invalid AI output.
* [x] Prevent AI output from modifying resources outside the authenticated user's authorized project.
* [x] Review prompt-injection handling for user-controlled task titles, descriptions, tags, and project data.
* [x] Add request size limits.
* [x] Add conversation/history limits.
* [x] Add appropriate rate limiting to expensive AI operations.
* [x] Add timeout and controlled retry behavior.
* [x] Ensure AI failures cannot corrupt persisted board state.

### API & Input Security

* [x] Audit all FastAPI endpoints.
* [x] Validate all request payloads using strict Pydantic models.
* [x] Replace unrestricted role/priority strings with enums where appropriate.
* [x] Add sensible maximum lengths for usernames, project names, task titles, descriptions, tags, and AI messages.
* [x] Validate pagination parameters.
* [x] Enforce maximum pagination limits.
* [x] Prevent oversized request payloads.
* [x] Review SQL query construction and parameterization.
* [x] Review file/path handling if applicable.
* [x] Review error responses for information leakage.
* [x] Ensure internal exceptions are logged server-side without exposing stack traces to clients.

### CORS & Deployment Security

* [x] Review production CORS configuration.
* [x] Ensure production does not rely on wildcard CORS when credentials are involved.
* [x] Restrict production origins to the actual frontend deployment.
* [x] Review all production environment variables.
* [x] Ensure secrets are never committed to Git.
* [x] Ensure `.env` files containing secrets remain excluded from version control.
* [x] Ensure production secrets are required rather than silently falling back to development values.
* [x] Verify HTTPS/WSS behavior in the deployed environment.
* [x] Verify Vercel frontend and Render backend configuration.
* [x] Verify production WebSocket connectivity.

### Rate Limiting & Abuse Protection

* [x] Audit the existing rate limiter.
* [x] Ensure expired rate-limit entries do not grow without bound.
* [x] Protect authentication endpoints from brute-force attempts.
* [x] Protect AI endpoints from abuse.
* [x] Review proxy/IP handling for deployed infrastructure.
* [x] Document limitations of in-memory rate limiting.
* [x] If the current architecture cannot support distributed rate limiting, document the limitation rather than pretending it does.

### Database Integrity & Concurrency

* [x] Verify SQLite foreign-key enforcement.
* [x] Review transaction boundaries.
* [x] Review rollback behavior.
* [x] Review database connection lifecycle.
* [x] Review concurrent write behavior.
* [x] Review board update race conditions.
* [x] Prevent stale client state from overwriting newer persisted state where practical.
* [x] Review database indexes for frequently queried fields.
* [x] Review migration behavior.
* [x] Ensure database migrations are deterministic.
* [x] Document SQLite production limitations.

### Frontend Security & State

* [x] Audit all `localStorage` and `sessionStorage` usage.
* [x] Remove sensitive authentication data from browser storage where inappropriate.
* [x] Ensure logout clears user-specific cached state.
* [x] Verify project switching cannot display stale data from another project.
* [x] Review optimistic updates for stale-request overwrites.
* [x] Review rapid drag-and-drop persistence.
* [x] Review WebSocket updates interacting with optimistic local state.
* [x] Ensure failed requests correctly roll back local state.
* [x] Ensure old API responses cannot overwrite newer board state.

### Security Regression Tests

Add automated tests for every security issue discovered during this audit.

Minimum required tests:

* [x] Unauthenticated API access is rejected.
* [x] Client cannot impersonate another username.
* [x] Invalid/expired authentication credentials are rejected.
* [x] Logout invalidates authentication.
* [x] Passwords are never persisted in browser storage.
* [x] User A cannot access User B's project.
* [x] User A cannot access User B's cards.
* [x] User A cannot access User B's notifications.
* [x] User A cannot access User B's activity history.
* [x] Unauthorized project membership changes are rejected.
* [x] Viewers cannot mutate board state.
* [x] Unauthorized WebSocket connections are rejected.
* [x] Unauthorized WebSocket messages are rejected.
* [x] AI cannot mutate another user's project.
* [x] Invalid AI mutation payloads are rejected.
* [x] Oversized AI requests are rejected.
* [x] Authentication rate limiting works.
* [x] AI rate limiting works.
* [x] Pagination limits are enforced.
* [x] Malformed requests return safe errors.
* [x] Production configuration does not expose development credentials.

### Tests & Verification

* [x] Run the complete backend test suite.
* [x] Run the complete frontend test suite.
* [x] Run the complete Playwright E2E suite.
* [x] Run all newly added security regression tests.
* [x] Run dependency/security audits.
* [x] Run production frontend build.
* [x] Build the production Docker image.
* [x] Start the production container locally.
* [x] Verify backend health endpoint.
* [x] Verify frontend-to-backend communication.
* [x] Verify authentication end-to-end.
* [x] Verify authorization end-to-end.
* [x] Verify multi-user isolation.
* [x] Verify WebSocket authentication and isolation.
* [x] Verify AI functionality after security changes.
* [x] Verify mobile functionality remains intact.
* [x] Verify existing Parts 1 through 25 functionality remains intact.

### Required Audit Report

After implementation, produce a security audit report containing:

1. Executive summary.
2. All discovered findings.
3. Severity classification:

   * P0: Production/security blocker
   * P1: Serious issue
   * P2: Important improvement
   * P3: Minor/polish
4. Affected file and function for each finding.
5. Impact of each finding.
6. Remediation performed.
7. Regression test covering each remediation.
8. Remaining known limitations.
9. Production infrastructure limitations.
10. Final security assessment.

Do not claim a finding is resolved unless the implementation and corresponding test have been verified.

### Success Criteria

* No critical authentication vulnerabilities remain.
* No client-controlled username can establish identity.
* Passwords are never stored in plaintext or browser storage.
* Authentication credentials are securely generated and validated.
* Protected resources enforce server-side authorization.
* Cross-user and cross-project access is prevented.
* WebSocket connections enforce authentication and project authorization.
* AI-generated mutations cannot bypass authorization or backend validation.
* Production configuration does not expose development credentials.
* Security regression tests pass.
* Existing functionality remains intact.
* All critical findings are either resolved or explicitly documented with a justified limitation.
* The application is ready to proceed to final production re-validation.

## Part 27: Final Re-Validation & Release Sign-Off

Re-run the final production validation after completion of Part 26.

### Tests & Verification

* [x] Run complete backend test suite.
* [x] Run complete frontend test suite.
* [x] Run complete Playwright E2E suite.
* [x] Run all security regression tests.
* [x] Build production frontend.
* [x] Build production Docker image.
* [x] Start and verify production container locally.
* [x] Verify authentication and logout.
* [x] Verify multi-user isolation.
* [x] Verify RBAC permissions.
* [x] Verify project and task CRUD.
* [x] Verify drag-and-drop persistence.
* [x] Verify undo/redo.
* [x] Verify AI task operations.
* [x] Verify AI project intelligence.
* [x] Verify WebSocket collaboration.
* [x] Verify notifications.
* [x] Verify mobile workflows.
* [x] Verify production environment configuration.
* [x] Verify deployed frontend/backend communication.
* [x] Verify deployed WebSocket connectivity.
* [x] Review production logs for errors.
* [x] Review documentation against the final implementation.
* [x] Confirm no known P0 or unresolved critical P1 issues remain.

### Required Final Report

Provide:

* Total tests executed.
* Total tests passed.
* Total tests failed.
* Security tests executed.
* Production build status.
* Docker build status.
* Deployment verification status.
* Remaining known limitations.
* Final list of unresolved issues.
* Final production-readiness classification.

Use exactly one final classification:

* NOT READY
* MVP READY
* PORTFOLIO READY
* PRODUCTION READY

Do not select PRODUCTION READY if any unresolved P0 security issue or critical data-integrity issue remains.

### Success Criteria

* All critical tests pass.
* Production build succeeds.
* Production container starts successfully.
* Authentication and authorization are verified.
* Multi-user isolation is verified.
* Real-time collaboration is verified.
* AI operations remain secure.
* No known critical security or data-integrity issues remain.
* Documentation accurately reflects the final implementation.
* Parts 1 through 26 remain intact unless a documented security correction required changing earlier behavior.
* The project receives a final release-readiness decision based on evidence rather than assumptions.

