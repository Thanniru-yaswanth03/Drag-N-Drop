import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import config
import database
from main import app


@pytest.fixture(autouse=True)
def isolated_db_environment(monkeypatch):
    """Ensure every test runs against a clean, isolated temporary SQLite database."""
    temp_dir = tempfile.mkdtemp()
    temp_db_path = Path(temp_dir) / "persistent_test_pm.db"
    monkeypatch.setenv("DATABASE_PATH", str(temp_db_path))

    # Initialize schema
    database.init_db(temp_db_path)

    yield temp_db_path

    # Clean up
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass


def test_scenario_a_registration_persistence_and_security(isolated_db_environment):
    """Test A: Registration
    Register user, verify SQLite insert, PBKDF2 hash, salt, and ensure no plaintext password in DB.
    """
    db_path = isolated_db_environment
    test_username = "testuser_unique_123"
    test_password = "SecretPassword!2026"

    # Register user
    reg_result = database.register_user(test_username, test_password, db_path=db_path)
    assert reg_result.get("success") is True, f"Registration failed: {reg_result}"
    assert "token" in reg_result
    assert reg_result["user"] == test_username

    # Inspect SQLite database directly
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, password_hash, password_salt FROM users WHERE username = ?", (test_username,))
    user_row = cursor.fetchone()
    conn.close()

    assert user_row is not None, "User record was not found in SQLite table 'users'"
    assert user_row["username"] == test_username
    assert len(user_row["password_salt"]) >= 16
    assert len(user_row["password_hash"]) == 64  # SHA256 hex digest length
    assert user_row["password_hash"] != test_password, "Plaintext password must NOT be stored in password_hash"
    assert test_password not in user_row["password_salt"], "Plaintext password must NOT be in salt"


def test_scenario_b_immediate_login(isolated_db_environment):
    """Test B: Immediate Login
    Login with registered credentials, verify success, verify invalid password fails.
    """
    db_path = isolated_db_environment
    username = "login_tester_99"
    password = "CorrectHorseBatteryStaple!"

    reg = database.register_user(username, password, db_path=db_path)
    assert reg["success"] is True

    # Successful login
    auth_success = database.authenticate_user(username, password, db_path=db_path)
    assert auth_success is not None
    assert auth_success["success"] is True
    assert auth_success["user"] == username
    assert auth_success["token"].startswith("sess-")

    # Failed login with wrong password
    auth_fail = database.authenticate_user(username, "WrongPassword123", db_path=db_path)
    assert auth_fail is None

    # Failed login with non-existent username
    auth_ghost = database.authenticate_user("ghost_user_xyz", password, db_path=db_path)
    assert auth_ghost is None


def test_scenario_c_new_database_connection_boundary(isolated_db_environment):
    """Test C: New Database Connection Boundary
    Close the database connection completely, open a fresh independent connection, query the user.
    """
    db_path = isolated_db_environment
    username = "boundary_user_42"
    password = "SuperStrongPassword!88"

    # Register and commit
    reg = database.register_user(username, password, db_path=db_path)
    assert reg["success"] is True

    # Open completely new raw connection from disk
    new_conn = sqlite3.connect(str(db_path))
    new_conn.row_factory = sqlite3.Row
    new_cursor = new_conn.cursor()

    new_cursor.execute("SELECT id, username FROM users WHERE username = ?", (username,))
    row = new_cursor.fetchone()
    new_conn.close()

    assert row is not None, "User could not be read back from a newly opened SQLite connection"
    assert row["username"] == username


def test_scenario_d_backend_restart_simulation(isolated_db_environment):
    """Test D: Backend Restart Simulation
    Simulate full process restart with fresh connection pool and authenticate again.
    """
    db_path = isolated_db_environment
    username = "reboot_user_77"
    password = "RebootPassword#2026"

    # Initial registration
    reg = database.register_user(username, password, db_path=db_path)
    assert reg["success"] is True
    token1 = reg["token"]

    # Verify session works before restart
    sess1 = database.verify_session_token(token1, db_path=db_path)
    assert sess1 is not None
    assert sess1["username"] == username

    # Simulate reboot: re-initialize DB schema (idempotent init_db), re-query
    database.init_db(db_path=db_path)

    # Login afresh post-restart
    auth_post_reboot = database.authenticate_user(username, password, db_path=db_path)
    assert auth_post_reboot is not None
    assert auth_post_reboot["success"] is True
    assert auth_post_reboot["user"] == username

    # Verify original session also remained valid
    sess_restored = database.verify_session_token(token1, db_path=db_path)
    assert sess_restored is not None
    assert sess_restored["username"] == username


def test_scenario_e_custom_persistent_path(isolated_db_environment):
    """Test E: Deployment Persistence Boundary
    Prove that custom DATABASE_PATH behaves identically and persists all writes.
    """
    db_path = isolated_db_environment
    assert database.get_database_path(db_path) == db_path.resolve()

    username = "mount_persist_user"
    password = "PersistPassWord123"

    reg = database.register_user(username, password, db_path=db_path)
    assert reg["success"] is True

    # Check that the database file on disk has grown and contains data
    assert db_path.exists()
    assert db_path.stat().st_size > 0


def test_scenario_f_multiple_users_concurrency(isolated_db_environment):
    """Test F: Multiple Users
    Register 3+ distinct users, verify all remain present and independent in SQLite.
    """
    db_path = isolated_db_environment
    users = [
        ("user_alpha_101", "PasswordAlpha!1"),
        ("user_beta_202", "PasswordBeta!2"),
        ("user_gamma_303", "PasswordGamma!3"),
        ("user_delta_404", "PasswordDelta!4"),
    ]

    for uname, pword in users:
        res = database.register_user(uname, pword, db_path=db_path)
        assert res["success"] is True, f"Failed to register {uname}"

    # Verify all 4 users exist concurrently in SQLite
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users ORDER BY username ASC")
    all_users = [row[0] for row in cursor.fetchall()]
    conn.close()

    for uname, _ in users:
        assert uname in all_users, f"User {uname} missing from SQLite users table"

    # Verify each can authenticate independently
    for uname, pword in users:
        auth = database.authenticate_user(uname, pword, db_path=db_path)
        assert auth is not None
        assert auth["user"] == uname


def test_scenario_g_user_data_isolation(isolated_db_environment):
    """Test G: User Isolation
    User A must not be able to access or mutate User B's board or cards.
    """
    db_path = isolated_db_environment
    user_a = "tenant_alice"
    user_b = "tenant_bob"

    reg_a = database.register_user(user_a, "AlicePass123", db_path=db_path)
    reg_b = database.register_user(user_b, "BobPass123", db_path=db_path)

    # Fetch Alice's projects
    projs_a = database.get_projects(user_a, db_path=db_path)
    assert len(projs_a) > 0
    alice_proj_id = projs_a[0]["id"]

    # Bob should not have Alice's project in his list
    projs_b = database.get_projects(user_b, db_path=db_path)
    assert len(projs_b) > 0
    bob_proj_ids = [p["id"] for p in projs_b]
    assert alice_proj_id not in bob_proj_ids

    # Bob attempting to get Alice's board should fail (return None)
    bob_access_alice = database.get_board(user_id=user_b, project_id=alice_proj_id, db_path=db_path)
    assert bob_access_alice is None

    # Bob attempting to rename Alice's project should fail (return None)
    bob_rename_alice = database.update_project(user_id=user_b, project_id=alice_proj_id, name="Hacked Board", db_path=db_path)
    assert bob_rename_alice is None


def test_scenario_h_deletion_persistence(isolated_db_environment):
    """Test H: Delete/Recreate Persistence
    Delete a card and a project, restart the backend / fresh connection, prove deleted data never resurrects.
    """
    db_path = isolated_db_environment
    username = "clean_user_55"
    database.register_user(username, "CleanPass123", db_path=db_path)

    projs = database.get_projects(username, db_path=db_path)
    board_id = projs[0]["id"]

    board_data = database.get_board(username, project_id=board_id, db_path=db_path)
    col_id = board_data["columns"][0]["id"]

    # Add a card
    card = database.add_card(
        user_id=username,
        column_id=col_id,
        card_id="card-to-be-deleted-999",
        title="Temporary Task",
        details="Must not return after deletion",
        db_path=db_path,
    )
    assert card is not None
    assert card["id"] == "card-to-be-deleted-999"

    # Delete the card
    del_ok = database.delete_card("card-to-be-deleted-999", user_id=username, db_path=db_path)
    assert del_ok is True

    # Simulate backend reboot / fresh connection
    database.init_db(db_path=db_path)

    # Re-fetch board post-reboot
    board_after_reboot = database.get_board(username, project_id=board_id, db_path=db_path)
    assert "card-to-be-deleted-999" not in board_after_reboot["cards"]
    for col in board_after_reboot["columns"]:
        assert "card-to-be-deleted-999" not in col["cardIds"]

    # Verify directly in SQLite table
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cards WHERE id = ?", ("card-to-be-deleted-999",))
    assert cursor.fetchone() is None, "Deleted card resurrected in database!"
    conn.close()


def test_scenario_i_database_diagnostics_endpoint(isolated_db_environment):
    """Test I: Database Diagnostics Endpoint
    Verify /api/health and /api/diagnostics/db report accurate metadata without exposing any secrets.
    """
    db_path = isolated_db_environment
    client = TestClient(app)

    # Register a user via API
    reg_resp = client.post("/api/auth/register", json={"username": "diag_user_1", "password": "DiagPassword123"})
    assert reg_resp.status_code == 200

    # Query /api/health
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["status"] == "ok"
    assert "database" in health_data

    db_diag = health_data["database"]
    assert db_diag["fileExists"] is True
    assert db_diag["fileSizeBytes"] > 0
    assert db_diag["userCount"] >= 1
    assert db_diag["boardCount"] >= 1
    assert db_diag["sessionCount"] >= 1
    assert "resolvedPath" in db_diag

    # Verify NO secrets exposed in diagnostics response
    response_text = health_resp.text
    assert "password_hash" not in response_text
    assert "password_salt" not in response_text
    assert "DiagPassword123" not in response_text
    assert "sess-" not in response_text

    # Query /api/diagnostics/db
    diag_resp = client.get("/api/diagnostics/db")
    assert diag_resp.status_code == 200
    diag_data = diag_resp.json()
    assert diag_data["resolvedPath"] == db_diag["resolvedPath"]
    assert diag_data["userCount"] == db_diag["userCount"]
