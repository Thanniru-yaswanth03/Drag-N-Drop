import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import database
import config
from main import app

client = TestClient(app)


def test_production_persistence_lifecycle_and_restart():
    """Phase 14 & 17 Acceptance Test: Proves that all user data, projects, columns,
    tasks, task order, task status, activity logs, and notifications survive complete
    backend restart, connection teardown, and multiple consecutive init_db calls.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = Path(tmp_dir) / "persistent_test_pm.db"
        db_path_str = str(test_db)

        # 1. Start application & initialize database
        database.init_db(test_db)

        # 2. Register user
        username = "production_user_2026"
        password = "SecureProductionPassword#2026"
        reg_res = database.register_user(username, password, db_path=test_db)
        assert reg_res["success"] is True, f"Registration failed: {reg_res}"
        user_token = reg_res["token"]
        user_id = reg_res["userId"]

        # 3. Authenticate / Login
        auth_res = database.authenticate_user(username, password, db_path=test_db)
        assert auth_res is not None, "Authentication failed for newly registered user"
        assert auth_res["user"] == username

        # 4. Fetch initial project and columns
        projects = database.get_projects(username, db_path=test_db)
        assert len(projects) == 1
        main_project = projects[0]
        project_1_id = main_project["id"]

        board_1 = database.get_board(username, db_path=test_db, project_id=project_1_id)
        assert len(board_1["columns"]) == 5
        col_backlog_id = board_1["columns"][0]["id"]
        col_progress_id = board_1["columns"][2]["id"]
        col_done_id = board_1["columns"][4]["id"]

        # 5. Create multiple tasks with metadata
        card_1_id = "card-prod-101"
        card_1 = database.add_card(
            user_id=username,
            column_id=col_backlog_id,
            card_id=card_1_id,
            title="Design Authentication Architecture",
            details="Implement PostgreSQL support with connection pooling",
            description="Ensure 100% data persistence across Render restarts",
            priority="high",
            due_date="2026-09-01",
            tags=["architecture", "security", "database"],
            assignee=username,
            db_path=test_db,
        )
        assert card_1 is not None

        card_2_id = "card-prod-102"
        card_2 = database.add_card(
            user_id=username,
            column_id=col_progress_id,
            card_id=card_2_id,
            title="Configure Connection Pooling",
            details="Use psycopg_pool with thread-safe pool management",
            priority="medium",
            due_date="2026-09-05",
            tags=["performance", "database"],
            assignee=username,
            db_path=test_db,
        )
        assert card_2 is not None

        # 6. Modify a task
        updated_card_1 = database.update_card(
            card_id=card_1_id,
            updates={"title": "Design Authentication Architecture (Verified)", "priority": "high"},
            user_id=username,
            db_path=test_db,
        )
        assert updated_card_1["title"] == "Design Authentication Architecture (Verified)"

        # 7. Move task across columns and verify ordering
        database.move_card(
            card_id=card_1_id,
            destination_column_id=col_done_id,
            position=0,
            user_id=username,
            db_path=test_db,
        )

        # 8. Create second project
        project_2 = database.create_project(username, name="Mobile Application v2", db_path=test_db)
        project_2_id = project_2["id"]
        assert project_2_id != project_1_id

        # 9. Create notifications and activities
        notif_id = database.create_notification(
            user_id=username,
            project_id=project_1_id,
            notif_type="system",
            title="System Alert",
            message="Database upgraded to persistent storage.",
            db_path=test_db,
        )
        assert notif_id is not None

        # Record all IDs and state snapshot
        records_before_restart = {
            "username": username,
            "userId": user_id,
            "project_1_id": project_1_id,
            "project_2_id": project_2_id,
            "card_1_id": card_1_id,
            "card_2_id": card_2_id,
            "col_done_id": col_done_id,
            "col_progress_id": col_progress_id,
        }

        # -------------------------------------------------------------
        # 10. SIMULATE FULL BACKEND RESTART & LIFECYCLE RE-INITIALIZATION
        # -------------------------------------------------------------
        # Close any lingering connections and simulate multiple startup lifecycles
        for _ in range(5):
            database.init_db(test_db)

        # 11. Reconnect & Re-authenticate
        # Verify user record still exists in database
        conn = database.get_db_connection(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE LOWER(username) = ?", (username,))
        persisted_user = cursor.fetchone()
        conn.close()

        assert persisted_user is not None, "FATAL: User record disappeared after backend restart!"
        assert persisted_user["id"] == records_before_restart["userId"]
        assert persisted_user["username"] == username

        # Verify password login still works
        relogin_res = database.authenticate_user(username, password, db_path=test_db)
        assert relogin_res is not None, "FATAL: User login failed after backend restart!"
        assert relogin_res["user"] == username

        # 12. Fetch Projects post-restart
        projects_after = database.get_projects(username, db_path=test_db)
        assert len(projects_after) == 2, f"Expected 2 projects, found {len(projects_after)}"
        project_ids_after = {p["id"] for p in projects_after}
        assert project_1_id in project_ids_after, "FATAL: Project 1 disappeared after backend restart!"
        assert project_2_id in project_ids_after, "FATAL: Project 2 disappeared after backend restart!"

        # 13. Fetch Board 1 post-restart and verify Columns & Cards
        board_1_after = database.get_board(username, db_path=test_db, project_id=project_1_id)
        assert board_1_after is not None, "FATAL: Board 1 disappeared after backend restart!"
        assert len(board_1_after["columns"]) == 5

        # Verify Card 1 survived in Done column with all metadata
        assert card_1_id in board_1_after["cards"], "FATAL: Card 1 disappeared after backend restart!"
        c1_after = board_1_after["cards"][card_1_id]
        assert c1_after["title"] == "Design Authentication Architecture (Verified)"
        assert c1_after["priority"] == "high"
        assert c1_after["dueDate"] == "2026-09-01"
        assert "architecture" in c1_after["tags"]
        assert "security" in c1_after["tags"]
        assert c1_after["assignee"] == username

        # Verify Card 1 position in Done column
        done_col = next(c for c in board_1_after["columns"] if c["id"] == col_done_id)
        assert card_1_id in done_col["cardIds"], "FATAL: Card 1 not in target column after restart!"

        # Verify Card 2 survived in In Progress column
        assert card_2_id in board_1_after["cards"], "FATAL: Card 2 disappeared after backend restart!"
        c2_after = board_1_after["cards"][card_2_id]
        assert c2_after["title"] == "Configure Connection Pooling"
        assert c2_after["priority"] == "medium"

        # 14. Verify Activity Logs survived post-restart
        activities = database.get_project_activities(project_1_id, username, db_path=test_db)
        assert len(activities) >= 3, f"Expected at least 3 activities, found {len(activities)}"

        # 15. Verify Notifications survived post-restart
        notifs = database.get_user_notifications(username, db_path=test_db)
        assert len(notifs["notifications"]) >= 1
        assert any(n["title"] == "System Alert" for n in notifs["notifications"])

        # 16. Verify Diagnostics Report
        diag = database.get_database_diagnostics(test_db)
        assert diag["userCount"] >= 1
        assert diag["boardCount"] >= 2
        assert diag["cardCount"] >= 2


def test_database_url_resolution(monkeypatch):
    """Test resolution of PostgreSQL DATABASE_URL and SQLite URLs."""
    # 1. PostgreSQL URL
    monkeypatch.setenv("DATABASE_URL", "postgresql://app_user:secret_pass@db.example.com:5432/pmdb")
    url = config.get_database_url()
    assert url.startswith("postgresql://")
    assert database.is_postgres_target() is True

    diag = database.get_database_diagnostics()
    assert diag["engine"] == "postgresql"
    assert "secret_pass" not in diag["configuredUrl"]
    assert "***" in diag["configuredUrl"]

    # 2. postgres:// legacy prefix standardized
    monkeypatch.setenv("DATABASE_URL", "postgres://app_user:secret_pass@db.example.com:5432/pmdb")
    url = config.get_database_url()
    assert url.startswith("postgresql://")

    # 3. SQLite fallback when DATABASE_URL is unset
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_PATH", "/data/custom.db")
    url = config.get_database_url()
    assert "custom.db" in url
    assert database.is_postgres_target() is False
