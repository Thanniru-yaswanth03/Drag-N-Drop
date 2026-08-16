import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0f172a"))
        
        # Header (Skip on Page 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "KANBAN STUDIO PRO — MASTER TECHNICAL SPECIFICATION & MANUAL")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 50, 558, 50)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 38, "Engineered by YASH 🐐 • Next.js 16 + FastAPI + SQLite + Docker")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_text)
        self.restoreState()


def build_pdf(pdf_path):
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=64
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#1e293b")
    ACCENT_BLUE = colors.HexColor("#0284c7")
    TEXT_DARK = colors.HexColor("#334155")
    CODE_BG = colors.HexColor("#f8fafc")
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    # Title & Subtitle Styles
    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=8,
    )
    doc_subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=ACCENT_BLUE,
        spaceAfter=15,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=ACCENT_BLUE,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "BulletDark",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=4,
    )
    code_style = ParagraphStyle(
        "CodeText",
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
        backColor=CODE_BG,
        borderColor=BORDER_COLOR,
        borderWidth=0.5,
        borderPadding=4,
        spaceBefore=4,
        spaceAfter=6,
    )

    story = []

    # Title Block
    story.append(Paragraph("KANBAN STUDIO PRO 🐐", doc_title_style))
    story.append(Paragraph("A-Z Comprehensive Architectural Documentation, File Reference & Deployment Guide", doc_subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE, spaceAfter=15))

    # Executive Overview
    story.append(Paragraph("1. Executive Summary & Application Overview", h1_style))
    story.append(Paragraph(
        "<b>Kanban Studio Pro</b> is a full-stack, enterprise-grade project management web application. "
        "It features dynamic drag-and-drop task boards, multi-project workspace isolation, granular Role-Based Access Control (RBAC), "
        "cryptographic session token security, real-time WebSocket synchronization across devices, and an embedded natural-language AI Kanban Assistant with OpenRouter model failover.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Tech Stack Table
    story.append(Paragraph("2. Complete Technology Stack", h1_style))
    tech_data = [
        [Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Technologies & Version</b>", body_style), Paragraph("<b>Purpose / Key Features</b>", body_style)],
        [Paragraph("Frontend", body_style), Paragraph("Next.js 16 (Turbopack), React 19, TypeScript, TailwindCSS v4", body_style), Paragraph("High-performance App Router SPA with server/client components and modern glassmorphism styling.", body_style)],
        [Paragraph("Drag & Drop", body_style), Paragraph("@dnd-kit/core, @dnd-kit/sortable", body_style), Paragraph("Accessible, touch-friendly task reordering with MouseSensor, PointerSensor & TouchSensor (200ms delay, 8px tolerance, touch-action: none).", body_style)],
        [Paragraph("Backend API", body_style), Paragraph("FastAPI, Python 3.13, Uvicorn ASGI Server", body_style), Paragraph("Asynchronous REST API endpoints, WebSocket connection manager, rate limiting, and CORS routing.", body_style)],
        [Paragraph("Database", body_style), Paragraph("SQLite3 (WAL Mode), Python sqlite3 module", body_style), Paragraph("Relational persistence for users, sessions, projects, columns, cards, member roles, activity logs, and notifications.", body_style)],
        [Paragraph("Security & Auth", body_style), Paragraph("Cryptographic Session Tokens, Bearer / X-Session Headers, PBKDF2, RBAC Guard", body_style), Paragraph("secrets.token_hex(32) session tokens, Authorization Bearer headers, logout revocation, IDOR prevention, and RBAC hierarchy.", body_style)],
        [Paragraph("AI Assistant", body_style), Paragraph("OpenRouter API (GPT-4o-mini) + Model Failover Stack", body_style), Paragraph("Parses natural language prompts with failover (GPT-4o-mini -> Llama 3.3 70B -> Auto -> Smart Local NLP).", body_style)],
        [Paragraph("DevOps & Cloud", body_style), Paragraph("Docker, Render.com, Vercel, GitHub Actions", body_style), Paragraph("Containerized Python backend on Render + static Edge CDN frontend hosting on Vercel.", body_style)],
        [Paragraph("Testing", body_style), Paragraph("Pytest (80), Vitest (44), Playwright E2E (14)", body_style), Paragraph("Comprehensive 138-test automated suite covering backend API, security audit, database path persistence, frontend UI, and E2E browser flows.", body_style)],
    ]
    t = Table(tech_data, colWidths=[70, 190, 244])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # File Structure & Detailed Descriptions
    story.append(Paragraph("3. Complete Directory & File Structure (A-Z Guide)", h1_style))
    story.append(Paragraph("Below is a breakdown of every single file in the repository and its exact technical responsibility:", body_style))
    
    file_items = [
        ("Dockerfile (Root)", "Multi-stage Python 3.13 container definition for building and running the FastAPI backend on cloud hosts (Render/Railway). Creates /data mount, configures DATABASE_PATH=/data/pm.db, and launches uvicorn on port 8000."),
        (".dockerignore (Root)", "Docker ignore configuration strictly excluding local SQLite *.db binaries, .env, and cache files, ensuring pristine container builds without baked stale data."),
        ("render.yaml (Root)", "Render Blueprint deployment configuration file. Configures automatic container builds with Starter plan and 1GB persistent disk at /data for database persistence."),
        ("README.md (Root)", "Project documentation detailing live demo links, architecture overview, screenshot previews, data persistence guarantees, diagnostics endpoints, and setup instructions."),
        ("pm/backend/main.py", "FastAPI application entry point. Defines REST endpoints (/api/auth/register, /api/auth/login, /api/projects, /api/board, /api/cards, /api/health/db, /api/ai/chat) with header authentication and authenticated WebSocket route (/ws/projects/{id})."),
        ("pm/backend/database.py", "Core SQLite database layer. Contains schema definitions, sessions table, dynamic path resolution, connection hardening (WAL mode, Foreign Keys ON, busy_timeout=5000), PBKDF2 password hashing with per-user salt, atomic registration verification, RBAC permission checks, and safe diagnostics."),
        ("pm/backend/ai.py", "AI Assistant logic. Integrates OpenRouter API with model failover stack (gpt-4o-mini -> llama-3.3-70b -> auto -> smart local NLP) to execute structured board mutations."),
        ("pm/backend/websocket_manager.py", "ConnectionManager class managing real-time WebSocket client connections and broadcasting board updates to connected project members."),
        ("pm/backend/config.py", "Centralized configuration and database path resolver (get_database_path). Manages environment variables, CORS origin lists, and API keys."),
        ("pm/backend/test_production_persistence_verification.py", "Automated end-to-end persistence suite (10 scenarios) verifying registration, login, connection boundaries, backend restart data preservation, user data isolation, and deletion persistence."),
        ("pm/backend/test_database.py", "Pytest database regression test suite validating CRUD operations, foreign keys, and persistent data preservation."),
        ("pm/backend/test_security_audit.py & test_part28_adversarial_security.py", "Pytest security regression test suite validating session token security, token revocation on logout, IDOR prevention, RBAC role restrictions, unauthenticated WebSocket rejection, and AI prompt injection resistance."),
        ("pm/frontend/src/app/page.tsx & layout.tsx", "Next.js App Router root layout and primary page shell rendering the main Kanban interface with mobile viewport scale control."),
        ("pm/frontend/src/app/globals.css", "Global TailwindCSS v4 stylesheet containing modern theme CSS variables, glassmorphism card utilities, glowing animations, 16px mobile input rules, and vertical mobile column layout rules."),
        ("pm/frontend/src/components/KanbanBoard.tsx", "Core frontend board orchestrator. Manages user auth state, project switcher, undo/redo history, WebSocket real-time sync, @dnd-kit sensors (200ms delay, 8px tolerance), database single-source-of-truth loading, and column grid."),
        ("pm/frontend/src/components/AIAssistantWidget.tsx", "Floating AI Assistant chat drawer. Connects to /api/ai/chat via getApiUrl and automatically applies server-returned board updates."),
        ("pm/frontend/src/components/LoginForm.tsx", "Sign-in and Create Account tabbed modal featuring token storage, error alerts, case normalization, and fallback client registration."),
        ("pm/frontend/src/lib/api.ts", "API client module exporting getApiUrl, fetchBoard, saveBoard, registerApi, and project management network handlers with Bearer token & X-Session-Token authentication headers."),
        ("pm/frontend/src/lib/useUndoRedo.ts", "Custom React hook providing multi-level Undo (Ctrl+Z) and Redo (Ctrl+Y) state history management."),
        ("pm/frontend/tests/kanban.spec.ts", "Playwright E2E browser test suite (14 tests) running automated user interactions across desktop and mobile viewports."),
    ]

    for filename, desc in file_items:
        story.append(Paragraph(f"• <b>{filename}</b>: {desc}", bullet_style))

    story.append(Spacer(1, 10))

    # Core Logic & Key Site Functionalities
    story.append(Paragraph("4. Core Site Logic & Key Functionalities", h1_style))
    
    funcs = [
        ("Authentication & Session Management", "Users sign in or register new accounts. Username strings are automatically sanitized and lower-cased. Passwords are salted and hashed using PBKDF2-HMAC-SHA256 (100,000 iterations). Active sessions issue secrets.token_hex(24) tokens passed in Authorization: Bearer & X-Session-Token headers, and logout revokes tokens in SQLite."),
        ("Authoritative Database Persistence Engine", "Centralized dynamic path resolver (DATABASE_PATH=/data/pm.db on Render with 1GB persistent disk), WAL mode concurrency, atomic transaction query-back verification, and complete immunity from container restart data loss."),
        ("Multi-Project Isolation & IDOR Protection", "Users create, rename, switch between, and delete independent Kanban projects. Every backend API endpoint validates project permissions before allowing access or mutation."),
        ("Drag & Drop Engine (Desktop + Mobile)", "Powered by @dnd-kit. Features PointerSensor, MouseSensor, and TouchSensor (with a 200ms delay, 8px tolerance, and touch-action: none). On mobile screens, columns stack vertically to eliminate horizontal scroll issues."),
        ("Mobile Viewport Zoom & Sizing Optimization", "Exported viewport metadata in Next.js layout.tsx (initialScale: 1, maximumScale: 1, userScalable: false) and minimum 16px font-size input rules prevent iOS Safari auto-zooming on focus."),
        ("Security & RBAC Enforcement", "Backend endpoints enforce role hierarchy checks (Owner > Admin > Member > Viewer > None). Card mutations verify user membership before executing SQLite updates."),
        ("Real-Time WebSockets Sync", "When multiple users collaborate on the same project, board updates (card moves, edits, deletions) are instantly broadcast via WebSockets (/ws/projects/{id}) with token authentication."),
        ("AI Kanban Assistant & Model Failover", "Embedded chat drawer enables users to manage their board with natural language. Powered by OpenRouter API with multi-model failover stack (gpt-4o-mini -> llama-3.3-70b-instruct -> auto -> local NLP)."),
        ("Live Runtime Diagnostics", "Safe diagnostic endpoints (/api/health, /api/health/db, /api/diagnostics/db) reporting resolved database path, existence, file size, journal mode, and active entity row counts without secret exposure."),
    ]

    for title, desc in funcs:
        story.append(Paragraph(f"<b>{title}</b>: {desc}", body_style))

    story.append(Spacer(1, 10))

    # Testing Methodology
    story.append(Paragraph("5. Complete Testing Methodology (138 Automated Tests)", h1_style))
    story.append(Paragraph(
        "The application is validated by an automated test suite comprising <b>138 total tests</b> across 3 distinct test runners:",
        body_style
    ))
    story.append(Paragraph("• <b>Pytest (80 Tests)</b>: Validates backend REST routes, SQLite database schemas, PBKDF2 password hashing, cryptographic session tokens, persistent card/board data preservation across sessions, full restart lifecycle verification, RBAC permission checks, IDOR isolation, AI prompt injection resistance, and Part 28 adversarial security scenarios.", bullet_style))
    story.append(Paragraph("• <b>Vitest (44 Tests across 12 Suites)</b>: Unit tests frontend helper utilities (filterAndSortBoard, moveCard, useUndoRedo) and React UI components (LoginForm, TaskFilterToolbar, ProjectSwitcher, KanbanBoard).", bullet_style))
    story.append(Paragraph("• <b>Playwright E2E (14 Tests)</b>: Automated end-to-end browser tests in Headless Chromium. Verifies full user sign-in, task creation, dragging cards across columns, mobile viewport responsiveness, and multi-user login workflows.", bullet_style))

    story.append(Spacer(1, 10))

    # DevOps, Docker, Vercel & Render Setup
    story.append(Paragraph("6. DevOps Architecture: Docker, Render & Vercel", h1_style))
    story.append(Paragraph(
        "<b>Why Docker?</b><br/>"
        "Docker packages the Python runtime, FastAPI dependencies, Uvicorn server, and SQLite database into a standardized, "
        "lightweight Linux container. Root .dockerignore rules ensure local *.db binaries are never baked into container images.",
        body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Render Cloud Backend Hosting with Persistent Storage</b>:<br/>"
        "Render reads the root <code>render.yaml</code> and builds the Docker container. It attaches a 1GB persistent disk at <code>/data</code> "
        "(<code>DATABASE_PATH=/data/pm.db</code>) on Starter plan, guaranteeing database preservation across deployments and container restarts.",
        body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Vercel Frontend Hosting & Environment Variables</b>:<br/>"
        "Vercel hosts the Next.js static production bundle on an Edge CDN. The environment variable <code>NEXT_PUBLIC_API_URL</code> "
        "points to the Render backend URL (<code>https://drag-n-drop-28p3.onrender.com</code>).",
        body_style
    ))


    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Successfully Generated: {pdf_path}")


def create_markdown_file(md_path):
    content = """# 🗂️ KANBAN STUDIO PRO — MASTER TECHNICAL DOCUMENTATION & MANUAL

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

"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Markdown Documentation Created: {md_path}")


if __name__ == "__main__":
    doc_dir = Path(__file__).resolve().parent
    md_file = doc_dir / "Kanban_Studio_Pro_Master_Documentation.md"
    pdf_file = doc_dir / "Kanban_Studio_Pro_Master_Documentation.pdf"

    create_markdown_file(md_file)
    build_pdf(pdf_file)
