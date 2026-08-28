"""Seed realistic daily productivity tasks for all demo workspaces."""
from pathlib import Path
import sys
from datetime import datetime, timedelta

# Add current dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import database

def seed_daily_tasks():
    print("Seeding realistic daily productivity tasks...")
    database.init_db()

    demo_users = ["user", "yash", "alice", "bob"]

    sample_cards = [
        # Backlog
        {
            "col_idx": 0,
            "title": "Weekly team sprint planning & sync",
            "details": "Review priorities, assign upcoming milestone deliverables, and update the quarterly roadmap.",
            "priority": "medium",
            "due_days": 3,
            "tags": ["Planning", "Team"],
            "assignee": "yash",
        },
        {
            "col_idx": 0,
            "title": "Prepare monthly product metrics report",
            "details": "Aggregate active user metrics, conversion funnels, and retention graphs for leadership review.",
            "priority": "low",
            "due_days": 7,
            "tags": ["Analytics", "Report"],
            "assignee": "alice",
        },
        # Discovery
        {
            "col_idx": 1,
            "title": "Research customer feedback on mobile layout",
            "details": "Analyze user suggestions regarding touch interactions, swipe gestures, and responsiveness on tablets.",
            "priority": "medium",
            "due_days": 4,
            "tags": ["Research", "UX"],
            "assignee": "user",
        },
        {
            "col_idx": 1,
            "title": "Evaluate transactional notification providers",
            "details": "Benchmark deliverability, pricing tiers, and webhook latency across Resend and Postmark.",
            "priority": "low",
            "due_days": 10,
            "tags": ["DevOps", "Email"],
            "assignee": "bob",
        },
        # In Progress
        {
            "col_idx": 2,
            "title": "Refactor navigation header & quick shortcuts",
            "details": "Upgrade the Command Palette (Ctrl+K) and optimize keyboard navigation for fast task switching.",
            "priority": "high",
            "due_days": 1,
            "tags": ["Frontend", "Feature"],
            "assignee": "yash",
        },
        {
            "col_idx": 2,
            "title": "Optimize image assets and static bundling",
            "details": "Convert static assets to WebP/AVIF format and enable caching headers on CDN edge nodes.",
            "priority": "medium",
            "due_days": 2,
            "tags": ["Performance", "Web"],
            "assignee": "bob",
        },
        # Review
        {
            "col_idx": 3,
            "title": "Code Review: User profile & security settings",
            "details": "Verify validation constraints, token expiry checks, and responsive mobile form layout.",
            "priority": "high",
            "due_days": 1,
            "tags": ["Security", "Review"],
            "assignee": "alice",
        },
        # Done
        {
            "col_idx": 4,
            "title": "Launch Spatial Command Center design system",
            "details": "Completed modern 3D visual redesign with obsidian theme, amber accents, and fast micro-interactions.",
            "priority": "high",
            "due_days": -1,
            "tags": ["Design", "V1"],
            "assignee": "yash",
        },
        {
            "col_idx": 4,
            "title": "Configure automated CI/CD pipeline and tests",
            "details": "Configured full test suite verification and automatic deployment to production host.",
            "priority": "medium",
            "due_days": -2,
            "tags": ["DevOps", "CI"],
            "assignee": "bob",
        },
    ]

    for username in demo_users:
        projects = database.get_projects(username)
        if not projects:
            res = database.register_user(username, "password" if username in ("user", "yash") else "password123")
            projects = database.get_projects(username)

        if not projects:
            continue

        for proj in projects:
            project_id = proj["id"]
            board = database.get_board(username, project_id=project_id)
            if not board or not board.get("columns"):
                continue

            columns = board["columns"]
            
            # Clear out legacy / repetitive QA test cards from this board
            conn = database.get_db_connection()
            cursor = conn.cursor()
            col_ids = [c["id"] for c in columns]
            for col_id in col_ids:
                cursor.execute("DELETE FROM cards WHERE column_id = ?", (col_id,))
            conn.commit()
            conn.close()

            # Insert clean daily tasks
            today = datetime.now()
            for idx, item in enumerate(sample_cards):
                col_idx = item["col_idx"]
                if col_idx < len(columns):
                    target_col_id = columns[col_idx]["id"]
                    due_date = (today + timedelta(days=item["due_days"])).strftime("%Y-%m-%d")
                    card_id = f"card-{username[:3]}-{proj['id'][-4:]}-{idx+1}"
                    database.add_card(
                        user_id=username,
                        column_id=target_col_id,
                        card_id=card_id,
                        title=item["title"],
                        details=item["details"],
                        description=item["details"],
                        priority=item["priority"],
                        due_date=due_date,
                        tags=item["tags"],
                        assignee=item["assignee"],
                    )

            print(f"  [OK] Populated daily tasks for user '{username}' (Project: {proj['name']})")

    print("\nDaily tasks seeding complete!")

if __name__ == "__main__":
    seed_daily_tasks()
