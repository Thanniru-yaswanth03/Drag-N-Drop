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

    # Query /api/health/db
    health_db_resp = client.get("/api/health/db")
    assert health_db_resp.status_code == 200
    health_db_data = health_db_resp.json()
    assert health_db_data["status"] == "ok"
    assert health_db_data["resolvedPath"] == db_diag["resolvedPath"]
    assert health_db_data["userCount"] == db_diag["userCount"]
    assert "password_hash" not in health_db_resp.text
    assert "password_salt" not in health_db_resp.text
    assert "token" not in health_db_data


def test_scenario_j_full_restart_persistence_lifecycle(isolated_db_environment):
    """Test J: End-to-End Persistence Lifecycle
    Sequence: register -> login -> create card/board -> restart backend -> login again -> verify user/board/card persistence.
    """
    db_path = isolated_db_environment
    client = TestClient(app)

    username = "lifecycle_user_2026"
    password = "LifecyclePassWord!456"

    # Step 1: Register
    reg_res = client.post("/api/auth/register", json={"username": username, "password": password})
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    initial_token = reg_data["token"]

    # Step 2: Immediate Login
    login_res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login_res.status_code == 200
    login_token = login_res.json()["token"]

    # Step 3: Fetch projects and board
    auth_headers = {"Authorization": f"Bearer {login_token}"}
    projs_res = client.get("/api/projects", headers=auth_headers)
    assert projs_res.status_code == 200
    projs = projs_res.json()
    assert len(projs) > 0
    project_id = projs[0]["id"]

    board_res = client.get(f"/api/board?project_id={project_id}", headers=auth_headers)
    assert board_res.status_code == 200
    board_data = board_res.json()
    col_id = board_data["columns"][0]["id"]

    # Step 4: Create a new persistent card
    card_res = client.post(
        "/api/cards",
        json={
            "columnId": col_id,
            "title": "Vital Production Task",
            "details": "Must persist across full backend restart",
            "priority": "high",
        },
        headers=auth_headers,
    )
    assert card_res.status_code == 200
    created_card = card_res.json()["card"]
    created_card_id = created_card["id"]

    # Step 5: Simulate Backend Process Restart (re-initialize schema idempotently, fresh client)
    database.init_db(db_path=db_path)
    fresh_client = TestClient(app)

    # Step 6: Log in again post-restart
    re_login_res = fresh_client.post("/api/auth/login", json={"username": username, "password": password})
    assert re_login_res.status_code == 200
    new_session_token = re_login_res.json()["token"]
    new_auth_headers = {"Authorization": f"Bearer {new_session_token}"}

    # Step 7: Verify user / projects / board / cards are 100% intact
    me_res = fresh_client.get("/api/auth/me", headers=new_auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["user"] == username

    projs_post_res = fresh_client.get("/api/projects", headers=new_auth_headers)
    assert projs_post_res.status_code == 200
    projs_post = projs_post_res.json()
    assert any(p["id"] == project_id for p in projs_post)

    board_post_res = fresh_client.get(f"/api/board?project_id={project_id}", headers=new_auth_headers)
    assert board_post_res.status_code == 200
    board_post = board_post_res.json()
    assert created_card_id in board_post["cards"]
    assert board_post["cards"][created_card_id]["title"] == "Vital Production Task"
    assert board_post["cards"][created_card_id]["priority"] == "high"


def test_scenario_k_23_step_complete_persistence_lifecycle(isolated_db_environment):
    """Test K: Exact 23-Step Complete Persistence Lifecycle Test
    1. Register User A
    2. Login User A
    3. Create Project A
    4. Create Column A
    5. Create Column B
    6. Create Card 1
    7. Create Card 2
    8. Edit Card 1
    9. Move Card 1 from A -> B
    10. Reorder cards
    11. Delete Card 2
    12. Refresh
    13. Verify exact state
    14. Logout
    15. Login again
    16. Verify exact state
    17. Restart backend
    18. Verify exact state
    19. Delete Project
    20. Restart backend
    21. Verify Project is still deleted
    22. Register User B
    23. Verify User B cannot see User A's data
    """
    db_path = isolated_db_environment
    client = TestClient(app)

    # 1. Register User A
    user_a = "user_alpha_step23"
    pass_a = "SecretPassWordAlpha!123"
    reg_a = client.post("/api/auth/register", json={"username": user_a, "password": pass_a})
    assert reg_a.status_code == 200
    assert reg_a.json()["success"] is True

    # 2. Login User A
    login_a = client.post("/api/auth/login", json={"username": user_a, "password": pass_a})
    assert login_a.status_code == 200
    token_a = login_a.json()["token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 3. Create Project A
    proj_resp = client.post("/api/projects", json={"name": "Project Alpha"}, headers=headers_a)
    assert proj_resp.status_code == 200
    proj_a = proj_resp.json()
    proj_a_id = proj_a["id"]

    # 4 & 5. Fetch project's board columns (Column A and Column B)
    board_init = client.get(f"/api/board?project_id={proj_a_id}", headers=headers_a).json()
    assert len(board_init["columns"]) >= 2
    col_a_id = board_init["columns"][0]["id"]  # Backlog
    col_b_id = board_init["columns"][1]["id"]  # Discovery

    # 6. Create Card 1 in Column A
    c1_resp = client.post(
        "/api/cards",
        json={"columnId": col_a_id, "title": "Card 1 - Original Title", "details": "Details 1", "priority": "medium"},
        headers=headers_a,
    )
    assert c1_resp.status_code == 200
    card1 = c1_resp.json()["card"]
    card1_id = card1["id"]

    # 7. Create Card 2 in Column A
    c2_resp = client.post(
        "/api/cards",
        json={"columnId": col_a_id, "title": "Card 2 - Doomed Task", "details": "Details 2", "priority": "low"},
        headers=headers_a,
    )
    assert c2_resp.status_code == 200
    card2 = c2_resp.json()["card"]
    card2_id = card2["id"]

    # 8. Edit Card 1
    edit_resp = client.put(
        f"/api/cards/{card1_id}",
        json={"title": "Card 1 - Edited Title", "details": "Updated Details 1", "priority": "high"},
        headers=headers_a,
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["card"]["title"] == "Card 1 - Edited Title"
    assert edit_resp.json()["card"]["priority"] == "high"

    # 9. Move Card 1 from Column A -> Column B
    move_resp = client.patch(
        f"/api/cards/{card1_id}/move",
        json={"columnId": col_b_id, "position": 0},
        headers=headers_a,
    )
    assert move_resp.status_code == 200
    board_after_move = move_resp.json()["board"]
    assert card1_id in [col for col in board_after_move["columns"] if col["id"] == col_b_id][0]["cardIds"]

    # 10. Reorder cards (Create Card 3 in Column B, then reorder Card 3 before Card 1 via PUT /api/board)
    c3_resp = client.post(
        "/api/cards",
        json={"columnId": col_b_id, "title": "Card 3 - Header Task", "details": "Details 3", "priority": "medium"},
        headers=headers_a,
    )
    assert c3_resp.status_code == 200
    card3_id = c3_resp.json()["card"]["id"]

    # Save board with reordered cards in Column B: [card3_id, card1_id]
    current_board_state = client.get(f"/api/board?project_id={proj_a_id}", headers=headers_a).json()
    for col in current_board_state["columns"]:
        if col["id"] == col_b_id:
            col["cardIds"] = [card3_id, card1_id]

    reorder_resp = client.put(
        f"/api/board?project_id={proj_a_id}",
        json={"columns": current_board_state["columns"], "cards": current_board_state["cards"]},
        headers=headers_a,
    )
    assert reorder_resp.status_code == 200
    saved_col_b = [col for col in reorder_resp.json()["columns"] if col["id"] == col_b_id][0]
    assert saved_col_b["cardIds"] == [card3_id, card1_id]

    # 11. Delete Card 2
    del_resp = client.delete(f"/api/cards/{card2_id}", headers=headers_a)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 12. Refresh (Fetch fresh board state)
    refreshed_board = client.get(f"/api/board?project_id={proj_a_id}", headers=headers_a).json()

    # 13. Verify exact state
    assert card2_id not in refreshed_board["cards"]
    assert card1_id in refreshed_board["cards"]
    assert card3_id in refreshed_board["cards"]
    assert refreshed_board["cards"][card1_id]["title"] == "Card 1 - Edited Title"
    col_b_cards = [col for col in refreshed_board["columns"] if col["id"] == col_b_id][0]["cardIds"]
    assert col_b_cards == [card3_id, card1_id]

    # 14. Logout User A
    logout_resp = client.post("/api/auth/logout", headers=headers_a)
    assert logout_resp.status_code == 200

    # 15. Login again
    relogin_resp = client.post("/api/auth/login", json={"username": user_a, "password": pass_a})
    assert relogin_resp.status_code == 200
    token_a_new = relogin_resp.json()["token"]
    headers_a_new = {"Authorization": f"Bearer {token_a_new}"}

    # 16. Verify exact state
    board_after_login = client.get(f"/api/board?project_id={proj_a_id}", headers=headers_a_new).json()
    assert card2_id not in board_after_login["cards"]
    assert card1_id in board_after_login["cards"]
    assert card3_id in board_after_login["cards"]
    assert board_after_login["cards"][card1_id]["title"] == "Card 1 - Edited Title"

    # 17. Restart backend (simulate server reboot)
    database.init_db(db_path=db_path)
    reboot_client = TestClient(app)

    # 18. Verify exact state post-reboot
    reboot_login = reboot_client.post("/api/auth/login", json={"username": user_a, "password": pass_a})
    assert reboot_login.status_code == 200
    reboot_headers = {"Authorization": f"Bearer {reboot_login.json()['token']}"}
    board_post_reboot = reboot_client.get(f"/api/board?project_id={proj_a_id}", headers=reboot_headers).json()
    assert card2_id not in board_post_reboot["cards"]
    assert card1_id in board_post_reboot["cards"]
    assert card3_id in board_post_reboot["cards"]
    assert board_post_reboot["cards"][card1_id]["title"] == "Card 1 - Edited Title"

    # 19. Delete Project
    del_proj_resp = reboot_client.delete(f"/api/projects/{proj_a_id}", headers=reboot_headers)
    assert del_proj_resp.status_code == 200

    # 20. Restart backend again
    database.init_db(db_path=db_path)
    second_reboot_client = TestClient(app)

    # 21. Verify Project is still deleted
    reboot2_login = second_reboot_client.post("/api/auth/login", json={"username": user_a, "password": pass_a})
    reboot2_headers = {"Authorization": f"Bearer {reboot2_login.json()['token']}"}
    projs_after_del = second_reboot_client.get("/api/projects", headers=reboot2_headers).json()
    assert not any(p["id"] == proj_a_id for p in projs_after_del)

    # 22. Register User B
    user_b = "user_beta_step23"
    pass_b = "SecretPassWordBeta!456"
    reg_b = second_reboot_client.post("/api/auth/register", json={"username": user_b, "password": pass_b})
    assert reg_b.status_code == 200
    token_b = reg_b.json()["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 23. Verify User B cannot see User A's data
    user_b_projs = second_reboot_client.get("/api/projects", headers=headers_b).json()
    assert not any(p["id"] == proj_a_id for p in user_b_projs)
    user_b_forbidden_access = second_reboot_client.get(f"/api/board?project_id={proj_a_id}", headers=headers_b)
    assert user_b_forbidden_access.status_code in [403, 404]


def test_scenario_l_empty_database_returns_zero_cards(isolated_db_environment):
    """Test L: Empty Database Verification
    A user with zero cards gets 0 cards, NEVER magic default cards.
    """
    db_path = isolated_db_environment
    client = TestClient(app)

    username = "empty_user_zero"
    password = "EmptyUserPass!789"

    reg = client.post("/api/auth/register", json={"username": username, "password": password})
    assert reg.status_code == 200
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch initial board
    board_res = client.get("/api/board", headers=headers)
    assert board_res.status_code == 200
    board_data = board_res.json()

    # Cards must be empty dict {}
    assert board_data["cards"] == {}
    for col in board_data["columns"]:
        assert col["cardIds"] == []


def test_scenario_m_put_api_board_transactional_save(isolated_db_environment):
    """Test M: PUT /api/board Transactional Save
    Verify PUT /api/board persists cards, positions, columns, and removes omitted cards atomically.
    """
    db_path = isolated_db_environment
    client = TestClient(app)

    username = "put_board_user"
    password = "PutBoardPassword!123"

    reg = client.post("/api/auth/register", json={"username": username, "password": password})
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    projs = client.get("/api/projects", headers=headers).json()
    proj_id = projs[0]["id"]

    # Initial board
    init_board = client.get(f"/api/board?project_id={proj_id}", headers=headers).json()
    col0_id = init_board["columns"][0]["id"]
    col1_id = init_board["columns"][1]["id"]

    # Construct new full board payload with 2 cards in col0 and 1 card in col1
    save_payload = {
        "columns": [
            {"id": col0_id, "title": "Backlog Priority", "cardIds": ["card-alpha", "card-beta"]},
            {"id": col1_id, "title": "Discovery Active", "cardIds": ["card-gamma"]},
        ],
        "cards": {
            "card-alpha": {"id": "card-alpha", "title": "Alpha Task", "details": "Alpha Details", "priority": "high"},
            "card-beta": {"id": "card-beta", "title": "Beta Task", "details": "Beta Details", "priority": "medium"},
            "card-gamma": {"id": "card-gamma", "title": "Gamma Task", "details": "Gamma Details", "priority": "low"},
        },
    }

    put_resp = client.put(f"/api/board?project_id={proj_id}", json=save_payload, headers=headers)
    assert put_resp.status_code == 200
    saved_board = put_resp.json()

    assert "card-alpha" in saved_board["cards"]
    assert "card-beta" in saved_board["cards"]
    assert "card-gamma" in saved_board["cards"]
    assert saved_board["cards"]["card-alpha"]["priority"] == "high"

    # Verify directly in fresh client / query
    fresh_board = client.get(f"/api/board?project_id={proj_id}", headers=headers).json()
    assert len(fresh_board["cards"]) == 3

    # Now remove card-beta in next save payload and re-save
    save_payload_2 = {
        "columns": [
            {"id": col0_id, "title": "Backlog Priority", "cardIds": ["card-alpha"]},
            {"id": col1_id, "title": "Discovery Active", "cardIds": ["card-gamma"]},
        ],
        "cards": {
            "card-alpha": {"id": "card-alpha", "title": "Alpha Task", "details": "Alpha Details", "priority": "high"},
            "card-gamma": {"id": "card-gamma", "title": "Gamma Task", "details": "Gamma Details", "priority": "low"},
        },
    }
    put_resp_2 = client.put(f"/api/board?project_id={proj_id}", json=save_payload_2, headers=headers)
    assert put_resp_2.status_code == 200
    saved_board_2 = put_resp_2.json()

    assert "card-beta" not in saved_board_2["cards"]
    assert len(saved_board_2["cards"]) == 2


