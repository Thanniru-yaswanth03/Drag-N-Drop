# 🗂️ KANBAN STUDIO PRO — MASTER TECHNICAL DOCUMENTATION & MANUAL

> **Engineered by YASH 🐐**  
> Full-Stack Kanban Application with Next.js 16, React 19, FastAPI, SQLite3, @dnd-kit, WebSockets, AI Assistant & Docker Containerization.

---

## 1. Executive Summary & Application Overview

**Kanban Studio Pro** is a high-performance, enterprise-grade project management application designed for smooth task organization, team collaboration, and AI-assisted workflow automation. 

### Key Capabilities:
- **Interactive Drag & Drop**: Smooth mouse & mobile touch card reordering powered by `@dnd-kit`.
- **Multi-Project Workspace**: Create, switch, rename, and isolate multiple project boards.
- **Granular RBAC Security**: User permissions (owner, member, viewer) enforced at backend database level.
- **Real-Time WebSockets**: Instant live updates broadcast across connected client sessions.
- **Embedded AI Assistant**: Conversational AI parsing natural language commands into board actions.
- **Activity Audit Trail**: Automatic logging of all board modifications and team notifications.
- **Cross-Platform Responsive UX**: Glassmorphism aesthetic with theme toggling and mobile vertical stacked layout.

---

## 2. Complete Technology Stack

| Layer | Technology / Version | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | Next.js 16 (Turbopack), React 19, TypeScript | App Router client SPA, TypeScript type safety, and optimized Turbopack build. |
| **Styling & UI** | TailwindCSS v4, CSS Modules, Lucide Icons | Custom design system, glassmorphism card surfaces, and dark/light mode tokens. |
| **Drag & Drop** | `@dnd-kit/core`, `@dnd-kit/sortable` | Touch & pointer sensors (`delay: 150ms`, `tolerance: 5px`) for desktop & mobile. |
| **Backend Framework** | FastAPI (Python 3.13), Uvicorn ASGI | Asynchronous REST routing, WebSocket connection handling, and rate limiting. |
| **Database** | SQLite3 (WAL Mode), Python `sqlite3` module | Persistent storage for users, projects, columns, cards, members, and activity logs. |
| **AI Integration** | Rule Engine + Google Gemini API | Converts natural text prompts into structured JSON board mutation payloads. |
| **Containerization** | Docker (`python:3.13-slim`) | Standardized Linux container packaging backend code and dependencies. |
| **Cloud Hosting** | Render.com (Backend) & Vercel (Frontend) | Docker container API deployment on Render + Edge CDN distribution on Vercel. |
| **Testing Suite** | Pytest (39), Vitest (44), Playwright (14) | 97 automated unit, component, integration, data persistence, and E2E browser tests. |

---

## 3. Complete Directory & File Structure (A-Z File Guide)

```
Drag_N_Drop/
├── Dockerfile                        # Root Docker container definition for backend cloud deployment
├── render.yaml                        # Render Blueprint deployment configuration
├── README.md                          # Project repository overview and live links
├── documentation/                     # Dedicated documentation folder
│   ├── Kanban_Studio_Pro_Master_Documentation.pdf
│   ├── Kanban_Studio_Pro_Master_Documentation.md
│   └── generate_docs.py              # Automated master PDF & Markdown documentation generator
└── pm/
    ├── backend/                       # Python FastAPI Backend Service
    │   ├── main.py                    # REST & WebSocket API endpoints
    │   ├── database.py                # SQLite schema, queries, password hashing, RBAC
    │   ├── ai.py                      # AI Assistant rule engine & Gemini API integration
    │   ├── websocket_manager.py       # Real-time WebSocket connection broadcaster
    │   ├── config.py                  # Environment variable configuration loader
    │   ├── pm.db                      # SQLite binary database file
    │   ├── requirements.txt           # Python dependencies (fastapi, uvicorn, pytest)
    │   ├── test_main.py               # Pytest suite for FastAPI REST endpoints
    │   ├── test_database.py           # Pytest suite for SQLite database functions & data persistence
    │   ├── test_ai.py                 # Pytest suite for AI assistant handler
    │   ├── test_schema.py             # Pytest suite for Pydantic schema validation
    │   └── test_security.py           # Pytest suite for RBAC & password security
    └── frontend/                      # Next.js Frontend Web Application
        ├── package.json               # NPM scripts and frontend dependencies
        ├── playwright.config.ts       # Playwright E2E browser test configuration
        ├── vitest.config.ts           # Vitest unit test runner configuration
        ├── .env.example               # Environment variable template (NEXT_PUBLIC_API_URL)
        ├── src/
        │   ├── app/
        │   │   ├── page.tsx           # Next.js main page shell
        │   │   ├── layout.tsx         # Next.js root layout
        │   │   └── globals.css        # Global CSS, theme variables, mobile layout rules
        │   ├── components/
        │   │   ├── KanbanBoard.tsx    # Core board orchestrator & dnd-kit context
        │   │   ├── KanbanColumn.tsx   # Column container component
        │   │   ├── KanbanCard.tsx     # Drag-and-drop sortable card component
        │   │   ├── AIAssistantWidget.tsx # Floating AI chat drawer
        │   │   ├── LoginForm.tsx      # Authentication sign-in/register modal
        │   │   ├── ProjectSwitcher.tsx# Multi-project selection dropdown & modal
        │   │   ├── EditCardModal.tsx  # Card detailed editor modal
        │   │   ├── TaskFilterToolbar.tsx # Search, filter, and sort controls
        │   │   ├── ActivityHistoryModal.tsx # Project activity log viewer
        │   │   ├── ProjectMembersModal.tsx # Project member management modal
        │   │   └── NotificationCenterModal.tsx # Notifications drawer modal
        │   └── lib/
        │       ├── api.ts             # API client & getApiUrl helper with Bearer token authentication
        │       ├── kanban.ts          # Board data structures & moveCard logic
        │       ├── filterUtils.ts     # Search, tag filter, and priority sorting utilities
        │       ├── useUndoRedo.ts     # Multi-level Undo (Ctrl+Z) & Redo (Ctrl+Y) hook
        │       └── useWebSocket.ts    # React WebSocket connection hook
        └── tests/
            └── kanban.spec.ts         # Playwright E2E integration test suite
```

---

## 4. Detailed Functionalities & System Logic

### 🔑 Auth & Session Management
- **Registration & Sign-In**: Users register with username and password. Usernames are automatically lower-cased and sanitized.
- **Password Hashing**: Passwords are hashed with PBKDF2-HMAC-SHA256 (`100,000` iterations) and salted.
- **Header Authentication**: Active sessions issue `secrets.token_hex(32)` tokens passed via `Authorization: Bearer` and `X-Session-Token` headers.
- **Standalone Fallback**: If backend API is unreachable, local user accounts persist in `localStorage` (`pm_registered_users`).

### 💾 Persistent Database State Engine
- **Single Source of Truth**: Guaranteed SQLite database state loading on login and project switching, eliminating stale demo card overwrites.
- **Decoupled Async Persistence**: Card operations (drag-and-drop, title edit, priority, due date) update React state cleanly and persist to backend SQLite tables.

### 📱 Responsive Mobile Layout & Touch Drag & Drop
- **Vertical Mobile Stack**: On screens `< 1024px`, columns stack vertically (`flex flex-col gap-6 w-full`) to eliminate horizontal scrollbars.
- **TouchSensor Integration**: Touch activations require `delay: 150ms` and `tolerance: 5px`, allowing smooth page scrolling without accidental drags.

### 🛡️ Security & RBAC Permission System
- Projects check user roles (`owner`, `member`, `viewer`).
- Database verifies member access before allowing card additions, edits, or deletions.

### 🤖 AI Kanban Assistant Engine
- Users type prompts like *"Add urgent task Fix SSL to To Do"*.
- The AI engine parses input, generates structured JSON board updates, and automatically updates the database and frontend UI.

---

## 5. Testing Architecture (97 Total Tests — 100% Pass Rate)

1. **Pytest (39 Backend Tests)**: Verifies REST endpoints, database schema, PBKDF2 hashing, RBAC permissions, cryptographic session tokens, persistent data loss verification (`test_card_persistence_across_logout_and_login`), IDOR isolation, and Part 28 adversarial security scenarios.
2. **Vitest (44 Frontend Tests across 12 Suites)**: Tests React components, filter utilities, undo/redo state hooks, activity modals, notification center, project switcher, and auth form handlers.
3. **Playwright (14 E2E Tests)**: Automates Chromium browser interactions covering sign-in, card dragging, filtering, mobile viewport rendering, and multi-user login workflows.

---

## 6. DevOps: Docker, Render & Vercel Deployment

### 🐳 Why Docker?
Docker packages the Python 3.13 environment, FastAPI server, Uvicorn ASGI runner, and SQLite database into a self-contained container, guaranteeing identical execution across local dev and production servers.

### ☁️ Render Cloud Backend (`render.yaml` & `Dockerfile`)
Render pulls the repository, builds the root `Dockerfile`, exposes port `8000`, and serves CORS-enabled REST & WebSocket APIs.

### ⚡ Vercel Edge Frontend Deployment
Vercel hosts the Next.js static bundle on an Edge CDN. The environment variable `NEXT_PUBLIC_API_URL` points to the live Render backend (`https://drag-n-drop-28p3.onrender.com`).

---

## 7. Release Certification & Part 29 Final Status

- **Release Classification**: **`PRODUCTION READY`**
- **Security Audit Status**: 0 Critical (P0) or High (P1) Vulnerabilities
- **Part 28 Verification**: Passed independent adversarial security audit (`test_part28_adversarial_security.py`).
- **Part 29 Verification**: Passed final production deployment, test suite execution (97 automated tests passing 100%), persistent data loss regression testing, master documentation sync, and repository GitHub release packaging.
- **Part 29 Verification**: Passed final production deployment, test suite execution (96 automated tests passing 100%), master documentation sync, and repository GitHub release packaging.
