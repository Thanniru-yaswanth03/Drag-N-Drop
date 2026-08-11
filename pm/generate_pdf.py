import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Kanban Studio — Comprehensive Project Tutorial & Technical Documentation")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, footer_text)
        self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — KANBAN STUDIO MVP")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        
        self.restoreState()

def build_pdf(filename="Kanban_Studio_Project_Tutorial_and_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284C7"),
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=16,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0284C7"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F8FAFC"),
        borderColor=colors.HexColor("#E2E8F0"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # Cover Header
    story.append(Paragraph("🚀 Kanban Studio", title_style))
    story.append(Paragraph("Comprehensive Project Tutorial, System Architecture & Technical Documentation", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284C7"), spaceAfter=15))

    # Executive Overview
    story.append(Paragraph("1. Executive Overview & Project Description", h1_style))
    story.append(Paragraph(
        "<b>Kanban Studio</b> is an AI-powered, real-time multi-project task management system designed to emulate modern enterprise workflows. "
        "Built with a high-performance <b>FastAPI</b> backend, <b>SQLite</b> embedded database (WAL Mode), and a <b>Next.js / React 19</b> frontend, "
        "it enables teams to manage task cards across custom workflow columns with instant drag-and-drop mechanics, role-based authorization (RBAC), "
        "live WebSockets synchronization, due-date alerting, and analytical AI assistance.",
        body_style
    ))

    # Key Technology Stack
    story.append(Paragraph("2. Technology Stack & Frameworks", h1_style))
    
    tech_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Technologies Used", table_header_style), Paragraph("Key Purpose & Benefits", table_header_style)],
        [Paragraph("<b>Frontend Framework</b>", table_cell_style), Paragraph("React 19 / Next.js 16 (App Router)", table_cell_style), Paragraph("Server-side static rendering, fast client hydration, and clean component hierarchy.", table_cell_style)],
        [Paragraph("<b>Styling & UI</b>", table_cell_style), Paragraph("Tailwind CSS v4, Glassmorphism Tokens", table_cell_style), Paragraph("Curated color system for Light & Dark modes, WCAG AA contrast, responsive flex layouts.", table_cell_style)],
        [Paragraph("<b>Drag & Drop Engine</b>", table_cell_style), Paragraph("@dnd-kit/core, @dnd-kit/sortable", table_cell_style), Paragraph("Smooth hardware-accelerated drag mechanics with full keyboard accessibility.", table_cell_style)],
        [Paragraph("<b>Backend Framework</b>", table_cell_style), Paragraph("Python 3.13 / FastAPI", table_cell_style), Paragraph("Asynchronous RESTful APIs, OpenAPI auto-docs, Pydantic type safety.", table_cell_style)],
        [Paragraph("<b>Database</b>", table_cell_style), Paragraph("SQLite3 (WAL Mode & Compound Indexes)", table_cell_style), Paragraph("ACID-compliant relational persistence, zero-config deployment, optimized query speeds.", table_cell_style)],
        [Paragraph("<b>Real-Time Engine</b>", table_cell_style), Paragraph("FastAPI WebSockets (ws_manager)", table_cell_style), Paragraph("Instant state broadcasts to concurrent clients subscribing to project channels.", table_cell_style)],
        [Paragraph("<b>AI Engine</b>", table_cell_style), Paragraph("OpenRouter / Gemini 4o-mini / Local NLP", table_cell_style), Paragraph("Natural language card mutations, project summary reports, workload & overdue analysis.", table_cell_style)],
        [Paragraph("<b>Testing & Audit</b>", table_cell_style), Paragraph("Pytest, Vitest, Playwright E2E", table_cell_style), Paragraph("100% automated test coverage across unit, API, component, and user workflow levels.", table_cell_style)],
        [Paragraph("<b>Containerization</b>", table_cell_style), Paragraph("Docker, Multi-stage Docker Compose", table_cell_style), Paragraph("Self-contained production deployment bundling static assets and Python runtime.", table_cell_style)],
    ]

    tech_table = Table(tech_data, colWidths=[110, 160, 234])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # Feature Map
    story.append(Paragraph("3. Complete Feature Breakdown (Parts 1 – 25)", h1_style))

    features = [
        ("📋 Core Kanban & Card Drag-and-Drop", "Five workflow columns (Backlog, Discovery, In Progress, Review, Done) with smooth dnd-kit drag reordering and position persistence."),
        ("📝 Rich Task Metadata Editor", "Edit card title, details, long descriptions, priority levels (High/Medium/Low), due dates, assignees (@username), and tags (#tag)."),
        ("🔍 Filter, Search & Sort Toolbar", "Search cards instantly by title or details, filter by priority or assignee, sort by date/priority, and reset active filters with one click."),
        ("↩️ History Undo & Redo (Ctrl+Z / Ctrl+Y)", "Optimistic state management storing up to 20 historical snapshots. Supports both hotkeys and toolbar UI buttons."),
        ("🏢 Multi-Project Workspaces", "Create, switch, and delete independent project workspaces with isolated board configurations and permissions."),
        ("🛡️ Role-Based Access Control (RBAC)", "Hierarchical authorization (Owner > Admin > Member > Viewer) protecting board mutations, invitations, and deletions."),
        ("📜 Audit Activity Log", "Timestamped event tracking logging card creations, moves, updates, deletions, and member invitations per project."),
        ("⚡ WebSockets Real-Time Sync", "Live bi-directional WebSocket connection (/ws/projects/{project_id}) instantly syncing changes across active browser sessions."),
        ("🔔 Notification Center & Due-Date Alerting", "Automatic background scanner generating alerts for tasks due within 48 hours and drawer notification manager."),
        ("📊 AI Project Intelligence", "Analytical quick presets: Project Summary, Workload Analysis, Overdue Task Identification, and Re-Prioritization Suggestions."),
        ("🔐 Production Hardening & Security", "IP-based rate limiting on authentication routes (max 15/min), global exception masking, and secrets isolation."),
        ("⚡ Performance Optimizations", "React component memoization (KanbanCard, KanbanColumn), SQLite compound indexing, and paginated API endpoints.")
    ]

    for title, desc in features:
        story.append(Paragraph(f"<b>{title}</b>: {desc}", bullet_style))

    story.append(Spacer(1, 15))

    # Step-by-Step User Tutorial
    story.append(Paragraph("4. Step-by-Step User Tutorial & Guide", h1_style))

    tutorial_steps = [
        ("Step 1: Account Access & Login", "Open http://127.0.0.1:8000. Login with username 'user' or register a new user. Default workspace boards auto-seed upon first sign-in."),
        ("Step 2: Workspace & Project Navigation", "Use the top header dropdown to switch between projects or click '➕ New Project' to create an independent workspace."),
        ("Step 3: Creating and Dragging Cards", "Click '+ Add Card' in any column. Enter task title and details. Drag cards between columns to change state or reorder within a column."),
        ("Step 4: Editing Metadata & Assignees", "Click any card card to open the Edit Task Modal. Set priority (High/Medium/Low), due date, assignee, and tags."),
        ("Step 5: Inviting Team Members & Setting Roles", "Click '👥 Members' in the header. Enter a team member's username and assign their role (Owner, Admin, Member, Viewer)."),
        ("Step 6: Using AI Assistant & Intelligence", "Click the '✨ AI Assistant' widget in the bottom-right corner. Use quick buttons like '📊 Project Summary' or '👥 Workload' for instant AI analysis."),
        ("Step 7: Checking History & Alerts", "Click '📜 History' to review project activity logs or click '🔔 Alerts' to check upcoming due-date notifications.")
    ]

    for step, detail in tutorial_steps:
        story.append(Paragraph(f"<b>{step}</b>", h2_style))
        story.append(Paragraph(detail, body_style))

    story.append(Spacer(1, 10))

    # System Architecture & Database Design
    story.append(Paragraph("5. Database Schema & Architecture", h1_style))
    story.append(Paragraph(
        "The relational database schema is stored in <b>SQLite3</b> using WAL (Write-Ahead Logging) mode and compound indexes for high concurrency:",
        body_style
    ))

    db_schema_data = [
        [Paragraph("Table", table_header_style), Paragraph("Primary Columns", table_header_style), Paragraph("Indexes & Constraints", table_header_style)],
        [Paragraph("<b>users</b>", table_cell_style), Paragraph("id, username, password_hash, created_at", table_cell_style), Paragraph("PRIMARY KEY(id), UNIQUE(username)", table_cell_style)],
        [Paragraph("<b>boards</b>", table_cell_style), Paragraph("id, user_id, title, owner, created_at", table_cell_style), Paragraph("PRIMARY KEY(id), FOREIGN KEY(user_id)", table_cell_style)],
        [Paragraph("<b>columns</b>", table_cell_style), Paragraph("id, board_id, title, position", table_cell_style), Paragraph("PRIMARY KEY(id), FOREIGN KEY(board_id)", table_cell_style)],
        [Paragraph("<b>cards</b>", table_cell_style), Paragraph("id, column_id, title, details, priority, due_date, tags, assignee, position", table_cell_style), Paragraph("PRIMARY KEY(id), FOREIGN KEY(column_id), idx_cards_due_date", table_cell_style)],
        [Paragraph("<b>project_members</b>", table_cell_style), Paragraph("id, project_id, user_id, role, created_at", table_cell_style), Paragraph("UNIQUE(project_id, user_id), idx_project_members_user_project", table_cell_style)],
        [Paragraph("<b>activity_log</b>", table_cell_style), Paragraph("id, project_id, user_id, action_type, message, details, created_at", table_cell_style), Paragraph("idx_activity_log_project_created", table_cell_style)],
        [Paragraph("<b>notifications</b>", table_cell_style), Paragraph("id, user_id, project_id, type, title, message, is_read, created_at", table_cell_style), Paragraph("idx_notifications_user_read", table_cell_style)],
    ]

    db_table = Table(db_schema_data, colWidths=[100, 204, 200])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(db_table)
    story.append(Spacer(1, 15))

    # API Routes Summary
    story.append(Paragraph("6. REST & WebSocket API Endpoint Reference", h1_style))

    api_data = [
        [Paragraph("Method", table_header_style), Paragraph("Endpoint Path", table_header_style), Paragraph("Description & Function", table_header_style)],
        [Paragraph("POST", table_cell_style), Paragraph("/api/auth/login", table_cell_style), Paragraph("User authentication with rate limiting protection.", table_cell_style)],
        [Paragraph("POST", table_cell_style), Paragraph("/api/auth/register", table_cell_style), Paragraph("User registration & password hashing.", table_cell_style)],
        [Paragraph("GET", table_cell_style), Paragraph("/api/board", table_cell_style), Paragraph("Fetch project board structure (columns & cards).", table_cell_style)],
        [Paragraph("PUT", table_cell_style), Paragraph("/api/board", table_cell_style), Paragraph("Batch update board state (drag reordering).", table_cell_style)],
        [Paragraph("GET/POST", table_cell_style), Paragraph("/api/projects", table_cell_style), Paragraph("List user projects or create new workspace project.", table_cell_style)],
        [Paragraph("GET/POST", table_cell_style), Paragraph("/api/projects/{id}/members", table_cell_style), Paragraph("List or invite project team members (RBAC enforced).", table_cell_style)],
        [Paragraph("POST", table_cell_style), Paragraph("/api/ai/chat", table_cell_style), Paragraph("Process AI assistant commands & project intelligence.", table_cell_style)],
        [Paragraph("GET", table_cell_style), Paragraph("/api/activity-log", table_cell_style), Paragraph("Fetch paginated audit activity history log.", table_cell_style)],
        [Paragraph("GET", table_cell_style), Paragraph("/api/notifications", table_cell_style), Paragraph("Fetch paginated user notifications & due date alerts.", table_cell_style)],
        [Paragraph("WS", table_cell_style), Paragraph("/ws/projects/{id}", table_cell_style), Paragraph("Real-time WebSocket project change broadcast channel.", table_cell_style)],
    ]

    api_table = Table(api_data, colWidths=[65, 175, 264])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 15))

    # Deployment Guide
    story.append(Paragraph("7. Local Setup & Docker Deployment Guide", h1_style))
    story.append(Paragraph("Run the production stack locally using Docker Compose:", body_style))
    story.append(Paragraph(
        "<code># Build and launch production container stack\n"
        "docker-compose up --build -d\n\n"
        "# Verify backend health check\n"
        "curl http://localhost:8000/api/health</code>",
        code_style
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("8. Conclusion & Verification Summary", h1_style))
    story.append(Paragraph(
        "Kanban Studio is fully validated with <b>22 Pytest backend tests</b>, <b>44 Vitest frontend unit tests</b>, and <b>14 Playwright end-to-end workflow tests</b>. "
        "All 25 specification parts have been completed and verified for production readiness.",
        body_style
    ))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")

if __name__ == '__main__':
    build_pdf()
