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
- **Cross-Platform Responsive UX**: Glassmorphism aesthetic with theme toggling, mobile zoom prevention, and mobile vertical stacked layout.

---

## 2. Complete Technology Stack

| Layer | Technology / Version | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | Next.js 16 (Turbopack), React 19, TypeScript | App Router client SPA, TypeScript type safety, and optimized Turbopack build. |
| **Styling & UI** | TailwindCSS v4, CSS Modules, Lucide Icons | Custom design system, glassmorphism card surfaces, and dark/light mode tokens. |
| **Drag & Drop** | `@dnd-kit/core`, `@dnd-kit/sortable` | Touch & pointer sensors (`delay: 200ms`, `tolerance: 8px`, `touch-action: none`) for desktop & mobile. |
| **Backend Framework** | FastAPI (Python 3.13), Uvicorn ASGI | Asynchronous REST routing, WebSocket connection handling, and rate limiting. |
| **Database** | SQLite3 (WAL Mode, Foreign Keys ON, 5s timeout) | Persistent storage for users, projects, columns, cards, members, sessions, and activity logs. |
| **AI Integration** | OpenRouter API (GPT-4o-mini) + Model Failover Stack | Converts natural text prompts into structured JSON board mutation payloads. |
| **Containerization** | Docker (`python:3.13-slim`), Root `.dockerignore` | Standardized Linux container packaging with strict exclusion of local DB artifacts. |
| **Cloud Hosting** | Render.com (Backend API with 1GB Persistent Disk) & Vercel (Frontend) | Persistent SQLite container API on Render + Edge CDN distribution on Vercel. |
| **Testing Suite** | Pytest (80), Vitest (44), Playwright (14) | 138 automated unit, component, integration, data persistence, and E2E browser tests. |

---

## 3. Complete Directory & File Structure (A-Z File Guide)

```
Drag_N_Drop/
├── Dockerfile                        # Root Docker container definition with /data persistent mount
├── .dockerignore                     # Docker ignore rules excluding *.db binaries and dev caches
├── render.yaml                        # Render Blueprint deployment with Starter persistent disk (/data)
├── README.md                          # Project repository overview and live links
├── documentation/                     # Dedicated documentation folder
│   ├── Kanban_Studio_Pro_Master_Documentation.pdf
│   ├── Kanban_Studio_Pro_Master_Documentation.md
│   └── generate_docs.py              # Automated master PDF & Markdown documentation generator
└── pm/
    ├── backend/                       # Python FastAPI Backend Service
    │   ├── main.py                    # REST & WebSocket API endpoints & /api/health/db diagnostic route
    │   ├── database.py                # SQLite schema, queries, PBKDF2 hashing, RBAC, safe diagnostics
    │   ├── ai.py                      # AI Assistant rule engine & Gemini API integration
    │   ├── websocket_manager.py       # Real-time WebSocket connection broadcaster
    │   ├── config.py                  # Dynamic database path resolver (get_database_path) & config loader
    │   ├── requirements.txt           # Python dependencies (fastapi, uvicorn, pytest, reportlab)
    │   ├── test_main.py               # Pytest suite for FastAPI REST endpoints
    │   ├── test_database.py           # Pytest suite for SQLite database functions & data persistence
    │   ├── test_production_persistence_verification.py # Automated end-to-end persistence suite (10 scenarios)
    │   ├── test_security_audit.py     # Pytest security audit suite
    │   └── test_part28_adversarial_security.py # Pytest adversarial security suite
    └── frontend/                      # Next.js Frontend Web Application
        ├── package.json               # NPM scripts and frontend dependencies
        ├── playwright.config.ts       # Playwright E2E browser test configuration
        ├── vitest.config.ts           # Vitest unit test runner configuration
        ├── .env.example               # Environment variable template (NEXT_PUBLIC_API_URL)
        ├── src/
        │   ├── app/
        │   │   ├── page.tsx           # Next.js main page shell
        │   │   ├── layout.tsx         # Next.js root layout with mobile viewport scale metadata
        │   │   └── globals.css        # Global CSS, theme variables, 16px mobile input rules
        │   ├── components/
        │   │   ├── KanbanBoard.tsx    # Core board orchestrator & dnd-kit context
        │   │   ├── KanbanColumn.tsx   # Column container component
        │   │   ├── KanbanCard.tsx     # Drag-and-drop sortable card component with touch-action: none
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
- **Password Hashing**: Passwords are hashed with PBKDF2-HMAC-SHA256 (`100,000` iterations) and salted per user with cryptographic random salts.
- **Header Authentication**: Active sessions issue `secrets.token_hex(24)` tokens passed via `Authorization: Bearer` and `X-Session-Token` headers.
- **Session Revocation**: Logout actively removes session tokens from SQLite.

### 💾 Persistent Database State Engine
- **Single Source of Truth**: Centralized dynamic database path resolver (`DATABASE_PATH=/data/pm.db` on Render with persistent disk).
- **Atomic Registration Verification**: Transactions commit and immediately verify user persistence with query-back validation.
- **Decoupled Async Persistence**: Card operations (drag-and-drop, title edit, priority, due date) persist cleanly to backend SQLite tables with WAL mode concurrency.

### 🩺 Live Runtime Diagnostics
- **Safe Health Endpoints**: `/api/health`, `/api/health/db`, and `/api/diagnostics/db` report resolved DB path, file size, journal mode, and row counts (`users`, `boards`, `cards`, `sessions`) with zero secret leakage.

### 📱 Responsive Mobile Layout & Touch Drag & Drop
- **Vertical Mobile Stack**: On screens `< 1024px`, columns stack vertically (`flex flex-col gap-6 w-full`) to eliminate horizontal scrollbars.
- **TouchSensor Integration**: Touch activations require `delay: 200ms` and `tolerance: 8px` with `touch-action: none` on card surfaces.
- **Mobile Viewport Zoom Prevention**: Next.js layout metadata + `-webkit-text-size-adjust: 100%` + minimum `16px` font-size on inputs.

---

## 5. Testing Architecture (138 Total Tests — 100% Pass Rate)

1. **Pytest (80 Backend Tests)**: Verifies REST endpoints, database schema, PBKDF2 hashing, RBAC permissions, cryptographic session tokens, persistent card/board data preservation across sessions, full restart lifecycle verification, IDOR isolation, and Part 28 adversarial security scenarios.
2. **Vitest (44 Frontend Tests across 12 Suites)**: Tests React components, filter utilities, undo/redo state hooks, activity modals, notification center, project switcher, and auth form handlers.
3. **Playwright (14 E2E Tests)**: Automates Chromium browser interactions covering sign-in, card dragging, filtering, mobile viewport rendering, and multi-user login workflows.

---

## 6. DevOps: Docker, Render & Vercel Deployment

### 🐳 Docker Containerization
Docker packages the Python 3.13 environment, FastAPI server, Uvicorn ASGI runner, and SQLite database into a self-contained container. Root `.dockerignore` excludes local DB files.

### ☁️ Render Cloud Backend (`render.yaml` & `Dockerfile`)
Render pulls the repository, builds the root `Dockerfile`, mounts a 1GB persistent disk at `/data` (`DATABASE_PATH=/data/pm.db`) on Starter plan, and serves CORS-enabled REST & WebSocket APIs at `https://drag-n-drop-28p3.onrender.com`.

### ⚡ Vercel Edge Frontend Deployment
Vercel hosts the Next.js static bundle on an Edge CDN. The environment variable `NEXT_PUBLIC_API_URL` points to the live Render backend (`https://drag-n-drop-28p3.onrender.com`).
Live URL: `https://drag-n-drop-lilac.vercel.app/`.

---

## 7. Release Certification Status

- **Release Classification**: **`PRODUCTION READY`**
- **Security Audit Status**: 0 Critical (P0) or High (P1) Vulnerabilities
- **Verification Suites**: Passed all 138 automated unit, security, and persistence lifecycle tests.

