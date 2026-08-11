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
        "real-time WebSocket synchronization across devices, and an embedded natural-language AI Kanban Assistant.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Tech Stack Table
    story.append(Paragraph("2. Complete Technology Stack", h1_style))
    tech_data = [
        [Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Technologies & Version</b>", body_style), Paragraph("<b>Purpose / Key Features</b>", body_style)],
        [Paragraph("Frontend", body_style), Paragraph("Next.js 16 (Turbopack), React 19, TypeScript, TailwindCSS v4", body_style), Paragraph("High-performance App Router SPA with server/client components and modern glassmorphism styling.", body_style)],
        [Paragraph("Drag & Drop", body_style), Paragraph("@dnd-kit/core, @dnd-kit/sortable", body_style), Paragraph("Accessible, touch-friendly task reordering with MouseSensor, PointerSensor & TouchSensor (150ms delay).", body_style)],
        [Paragraph("Backend API", body_style), Paragraph("FastAPI, Python 3.13, Uvicorn ASGI Server", body_style), Paragraph("Asynchronous REST API endpoints, WebSocket connection manager, rate limiting, and CORS routing.", body_style)],
        [Paragraph("Database", body_style), Paragraph("SQLite3 (WAL Mode), Python sqlite3 module", body_style), Paragraph("Relational persistence for users, projects, columns, cards, member roles, activity logs, and notifications.", body_style)],
        [Paragraph("AI Assistant", body_style), Paragraph("Custom Rule Engine & Google Gemini API", body_style), Paragraph("Parses natural language prompts to automatically execute structured board mutations (add, move, clear tasks).", body_style)],
        [Paragraph("DevOps & Cloud", body_style), Paragraph("Docker, Render.com, Vercel, GitHub Actions", body_style), Paragraph("Containerized Python backend on Render + static Edge CDN frontend hosting on Vercel.", body_style)],
        [Paragraph("Testing", body_style), Paragraph("Pytest (22), Vitest (44), Playwright E2E (14)", body_style), Paragraph("Comprehensive 80-test automated suite covering backend API, frontend UI, state logic, and browser flows.", body_style)],
    ]
    t = Table(tech_data, colWidths=[80, 180, 244])
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
        ("Dockerfile (Root)", "Multi-stage Python 3.13 container definition for building and running the FastAPI backend on cloud hosts (Render/Railway). Installs system dependencies, copies requirements, and launches uvicorn on port 8000."),
        ("render.yaml (Root)", "Render Blueprint deployment configuration file. Configures automatic container builds from root Dockerfile and passes CORS_ORIGINS and PORT environment variables."),
        ("README.md (Root)", "Project documentation detailing live demo links, architecture overview, screenshot previews, and setup instructions."),
        ("pm/backend/main.py", "FastAPI application entry point. Defines REST endpoints (/api/auth/register, /api/auth/login, /api/projects, /api/board, /api/cards, /api/ai/chat) and WebSocket route (/ws/projects/{id})."),
        ("pm/backend/database.py", "Core SQLite database layer. Contains schema definitions, table migrations, connection management, PBKDF2 password hashing, RBAC permission checks, CRUD operations, and default board seeding."),
        ("pm/backend/ai.py", "AI Assistant logic. Integrates Google Gemini API with fallbacks to execute structured board mutations (creating tasks, moving cards across columns, clearing completed items)."),
        ("pm/backend/websocket_manager.py", "ConnectionManager class managing real-time WebSocket client connections and broadcasting board updates to connected project members."),
        ("pm/backend/config.py", "Environment configuration loader for reading database paths, CORS origin lists, and API keys."),
        ("pm/backend/requirements.txt", "Backend Python dependencies list (fastapi, uvicorn, pydantic, pytest, google-generativeai)."),
        ("pm/backend/test_main.py & test_database.py", "Pytest backend test suite (22 tests) validating authentication, DB queries, card mutations, RBAC access checks, and AI response payloads."),
        ("pm/frontend/src/app/page.tsx & layout.tsx", "Next.js App Router root layout and primary page shell rendering the main Kanban interface."),
        ("pm/frontend/src/app/globals.css", "Global TailwindCSS v4 stylesheet containing modern theme CSS variables, glassmorphism card utilities, glowing animations, and vertical mobile column layout rules."),
        ("pm/frontend/src/components/KanbanBoard.tsx", "Core frontend board orchestrator. Manages user auth state, project switcher, undo/redo history, WebSocket real-time sync, @dnd-kit sensors, and column grid."),
        ("pm/frontend/src/components/KanbanColumn.tsx", "Droppable column container component rendering column headers, task counter badges, card lists, and quick-add task buttons."),
        ("pm/frontend/src/components/KanbanCard.tsx", "Sortable task card component with smooth hover micro-animations, priority tags, due dates, assignees, and quick edit/delete buttons."),
        ("pm/frontend/src/components/AIAssistantWidget.tsx", "Floating AI Assistant chat drawer. Connects to /api/ai/chat via getApiUrl and automatically applies server-returned board updates."),
        ("pm/frontend/src/components/LoginForm.tsx", "Sign-in and Create Account tabbed modal featuring auto-login, error alerts, case normalization, and fallback client registration."),
        ("pm/frontend/src/lib/api.ts", "API client module exporting getApiUrl, fetchBoard, saveBoard, registerApi, and project management network handlers."),
        ("pm/frontend/src/lib/kanban.ts", "Kanban data structures, immutability helpers, moveCard logic, and initial default board generator."),
        ("pm/frontend/src/lib/useUndoRedo.ts", "Custom React hook providing multi-level Undo (Ctrl+Z) and Redo (Ctrl+Y) state history management."),
        ("pm/frontend/tests/kanban.spec.ts", "Playwright E2E browser test suite (14 tests) running automated user interactions across desktop and mobile viewports."),
    ]

    for filename, desc in file_items:
        story.append(Paragraph(f"• <b>{filename}</b>: {desc}", bullet_style))

    story.append(Spacer(1, 10))

    # Core Logic & Key Site Functionalities
    story.append(Paragraph("4. Core Site Logic & Key Functionalities", h1_style))
    
    funcs = [
        ("Authentication & Case Normalization", "Users can sign in or register new accounts. Username strings are automatically sanitized and lower-cased to prevent case-sensitivity mismatches during authentication. Passwords are salted and hashed using PBKDF2-HMAC-SHA256."),
        ("Multi-Project Isolation", "Users can create, rename, switch between, and delete multiple independent Kanban projects. Each project retains its own isolated columns, cards, members, and activity log."),
        ("Drag & Drop Engine (Desktop + Mobile)", "Powered by @dnd-kit. Features PointerSensor, MouseSensor, and TouchSensor (with a 150ms delay and 5px tolerance). On mobile screens, columns stack vertically to eliminate horizontal scroll issues."),
        ("Security & RBAC Enforcement", "Backend endpoints enforce permission checks (owner vs member vs viewer). Card mutations verify user membership before executing SQLite updates."),
        ("Real-Time WebSockets Sync", "When multiple users collaborate on the same project, board updates (card moves, edits, deletions) are instantly broadcast via WebSockets (/ws/projects/{id})."),
        ("AI Kanban Assistant", "Embedded chat drawer enables users to manage their board with natural language (e.g. 'Move high priority tasks to In Progress')."),
        ("Activity Log & Notification System", "Every project action (adding cards, editing titles, changing priority) is logged in SQLite and presented in interactive modal dialogs."),
    ]

    for title, desc in funcs:
        story.append(Paragraph(f"<b>{title}</b>: {desc}", body_style))

    story.append(Spacer(1, 10))

    # Testing Methodology
    story.append(Paragraph("5. Complete Testing Methodology (80 Automated Tests)", h1_style))
    story.append(Paragraph(
        "The application is validated by an automated test suite comprising <b>80 total tests</b> across 3 distinct test runners:",
        body_style
    ))
    story.append(Paragraph("• <b>Pytest (22 Tests)</b>: Validates backend REST routes, SQLite database schemas, PBKDF2 password hashing, RBAC permission checks, and AI response structures.", bullet_style))
    story.append(Paragraph("• <b>Vitest (44 Tests)</b>: Unit tests frontend helper utilities (filterAndSortBoard, moveCard, useUndoRedo) and React UI components (LoginForm, TaskFilterToolbar, ProjectSwitcher).", bullet_style))
    story.append(Paragraph("• <b>Playwright E2E (14 Tests)</b>: Automated end-to-end browser tests in Headless Chromium. Verifies full user sign-in, task creation, dragging cards across columns, mobile viewport responsiveness, and multi-user login workflows.", bullet_style))

    story.append(Spacer(1, 10))

    # DevOps, Docker, Vercel & Render Setup
    story.append(Paragraph("6. DevOps Architecture: Docker, Render & Vercel", h1_style))
    story.append(Paragraph(
        "<b>Why Docker?</b><br/>"
        "Docker packages the Python runtime, FastAPI dependencies, Uvicorn server, and SQLite database into a standardized, "
        "lightweight Linux container. This eliminates 'it works on my machine' issues and ensures identical execution across local dev and cloud servers.",
        body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Render Cloud Backend Hosting</b>:<br/>"
        "Render reads the root <code>render.yaml</code> and builds the Docker container. It exposes port 8000 and serves CORS-enabled API requests. "
        "Note: Render free instances spin down after 15 minutes of inactivity; the initial request takes ~30 seconds for cold-start initialization.",
        body_style
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Vercel Frontend Hosting & Environment Variables</b>:<br/>"
        "Vercel hosts the Next.js static production bundle on an Edge CDN. The environment variable <code>NEXT_PUBLIC_API_URL</code> "
        "points to the Render backend URL (<code>https://drag-n-drop-28p3.onrender.com</code>). Because Next.js inlines <code>NEXT_PUBLIC_</code> "
        "variables at build time, updating this variable triggers a fresh Vercel rebuild to embed the live endpoint into the web app.",
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
| **Testing Suite** | Pytest (22), Vitest (44), Playwright (14) | 80 automated unit, component, integration, and E2E browser tests. |

---

## 3. Complete Directory & File Structure (A-Z File Guide)

```
Drag_N_Drop/
├── Dockerfile                        # Root Docker container definition for backend cloud deployment
├── render.yaml                        # Render Blueprint deployment configuration
├── README.md                          # Project repository overview and live links
├── documentation/                     # Dedicated documentation folder
│   ├── Kanban_Studio_Pro_Master_Documentation.pdf
│   └── Kanban_Studio_Pro_Master_Documentation.md
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
    │   ├── test_database.py           # Pytest suite for SQLite database functions
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
        │       ├── api.ts             # API client & getApiUrl helper
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
- **Standalone Fallback**: If backend API is unreachable, local user accounts persist in `localStorage` (`pm_registered_users`).

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

## 5. Testing Architecture (80 Total Tests)

1. **Pytest (22 Backend Tests)**: Verifies REST endpoints, database schema, PBKDF2 hashing, RBAC permissions, and AI payloads.
2. **Vitest (44 Frontend Tests)**: Tests React components, filter utilities, undo/redo state hooks, and auth form handlers.
3. **Playwright (14 E2E Tests)**: Automates Chromium browser interactions covering sign-in, card dragging, filtering, mobile viewport rendering, and multi-user login.

---

## 6. DevOps: Docker, Render & Vercel Deployment

### 🐳 Why Docker?
Docker packages the Python 3.13 environment, FastAPI server, Uvicorn ASGI runner, and SQLite database into a self-contained container, guaranteeing identical execution across local dev and production servers.

### ☁️ Render Cloud Backend (`render.yaml` & `Dockerfile`)
Render pulls the repository, builds the root `Dockerfile`, exposes port `8000`, and serves CORS-enabled REST & WebSocket APIs.

### ⚡ Vercel Edge Frontend Deployment
Vercel hosts the Next.js static bundle on an Edge CDN. The environment variable `NEXT_PUBLIC_API_URL` points to the live Render backend (`https://drag-n-drop-28p3.onrender.com`).
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
