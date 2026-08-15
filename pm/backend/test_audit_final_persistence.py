import pytest
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
import database
from main import app

TEST_DB_PATH = Path(__file__).resolve().parent / "test_pm_final_audit.db"
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass
    monkeypatch.setattr(database, "DB_PATH", TEST_DB_PATH)
    database.init_db(TEST_DB_PATH)
    yield
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass


def _register_user(username: str, password: str = "StrongPass123"):
    reg = client.post("/api/auth/register", json={"username": username, "password": password})
    assert reg.status_code == 200, f"Registration failed for {username}: {reg.text}"
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}", "X-Session-Token": token}
    return username, password, token, headers


# 1. Verification of No Auto-Seeding on Startup
def test_1_no_auto_seeding_on_startup():
    """Startup must only initialize schema/migrations and never auto-create default users."""
    conn = database.get_db_connection(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM boards")
    board_count = cursor.fetchone()["count"]
    cursor.execute("SELECT COUNT(*) as count FROM cards")
    card_count = cursor.fetchone()["count"]
    conn.close()

    assert user_count == 0, "No users should be auto-created on startup"
    assert board_count == 0, "No boards should be auto-created on startup"
    assert card_count == 0, "No cards should be auto-created on startup"


# 2. Registration Single Project Creation & Unique Username Enforced
def test_2_registration_integrity():
    u, p, token, headers = _register_user("alice_audit", "mypassword123")
    
    # Verify initial starter project created exactly once
    projects = client.get("/api/projects", headers=headers).json()
    assert len(projects) == 1
    assert projects[0]["name"] == "Main Project"

    # Duplicate registration must fail cleanly with 400
    dup_res = client.post("/api/auth/register", json={"username": "alice_audit", "password": "differentpassword"})
    assert dup_res.status_code == 400
    assert "already taken" in dup_res.json()["detail"].lower()

    # Original password remains intact
    auth_check = database.authenticate_user("alice_audit", "mypassword123", db_path=TEST_DB_PATH)
    assert auth_check is not None


# 3. Card Deletion Permanence (Deleted cards stay deleted across refresh, logout/login, and restart)
def test_3_card_deletion_permanence():
    u, p, token, headers = _register_user("bob_audit", "password123")
    board = client.get("/api/board", headers=headers).json()
    col_id = board["columns"][0]["id"]

    # 1. Create 3 cards
    c1_id = client.post("/api/cards", json={"columnId": col_id, "title": "Card 1"}, headers=headers).json()["card"]["id"]
    c2_id = client.post("/api/cards", json={"columnId": col_id, "title": "Card 2"}, headers=headers).json()["card"]["id"]
    c3_id = client.post("/api/cards", json={"columnId": col_id, "title": "Card 3"}, headers=headers).json()["card"]["id"]

    # 2. Delete Card 2
    del_res = client.delete(f"/api/cards/{c2_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify physical deletion in database
    conn = database.get_db_connection(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cards WHERE id = ?", (c2_id,))
    assert cursor.fetchone() is None, "Card record must be physically deleted from database"
    conn.close()

    # 3. Refresh 1: Query board via API
    refreshed_1 = client.get("/api/board", headers=headers).json()
    assert c2_id not in refreshed_1["cards"]
    assert c1_id in refreshed_1["cards"]
    assert c3_id in refreshed_1["cards"]

    # 4. Logout & Relogin
    client.post("/api/auth/logout", headers=headers)
    login_res = client.post("/api/auth/login", json={"username": u, "password": p})
    new_token = login_res.json()["token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    refreshed_2 = client.get("/api/board", headers=new_headers).json()
    assert c2_id not in refreshed_2["cards"]

    # 5. Backend Restart simulation (init_db on existing DB)
    database.init_db(TEST_DB_PATH)
    refreshed_3 = client.get("/api/board", headers=new_headers).json()
    assert c2_id not in refreshed_3["cards"]
    assert len(refreshed_3["cards"]) == 2


# 4. Project Deletion Permanence (Deleted projects stay deleted and are NOT resurrected)
def test_4_project_deletion_permanence():
    u, p, token, headers = _register_user("charlie_audit", "password123")
    projects = client.get("/api/projects", headers=headers).json()
    assert len(projects) == 1
    proj_id = projects[0]["id"]

    # Delete the only project
    del_res = client.delete(f"/api/projects/{proj_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify get_projects returns empty list and does NOT auto-create a new project
    remaining_projects = client.get("/api/projects", headers=headers).json()
    assert remaining_projects == [], "Deleted projects must stay deleted"

    # Backend restart simulation
    database.init_db(TEST_DB_PATH)
    remaining_after_restart = client.get("/api/projects", headers=headers).json()
    assert remaining_after_restart == [], "get_projects must NOT resurrect projects on restart"


# 5. Granular Card Operations: Add, Edit, Move Atomically
def test_5_granular_card_crud():
    u, p, token, headers = _register_user("dan_audit", "password123")
    board = client.get("/api/board", headers=headers).json()
    col_backlog = board["columns"][0]["id"]
    col_done = board["columns"][-1]["id"]

    # 1. Create
    add_res = client.post(
        "/api/cards",
        json={"columnId": col_backlog, "title": "Audit Task", "details": "Initial details", "priority": "high"},
        headers=headers
    )
    assert add_res.status_code == 200
    card_id = add_res.json()["card"]["id"]

    # 2. Update
    upd_res = client.put(
        f"/api/cards/{card_id}",
        json={"title": "Audit Task Renamed", "priority": "low"},
        headers=headers
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["card"]["title"] == "Audit Task Renamed"
    assert upd_res.json()["card"]["priority"] == "low"

    # 3. Move
    move_res = client.patch(
        f"/api/cards/{card_id}/move",
        json={"columnId": col_done, "position": 0},
        headers=headers
    )
    assert move_res.status_code == 200

    # Verify board state
    board_after = client.get("/api/board", headers=headers).json()
    done_col = next(c for c in board_after["columns"] if c["id"] == col_done)
    backlog_col = next(c for c in board_after["columns"] if c["id"] == col_backlog)
    assert card_id in done_col["cardIds"]
    assert card_id not in backlog_col["cardIds"]


# 6. Tenant Isolation: Cross-Tenant Access Strictly Forbidden
def test_6_tenant_isolation():
    u_a, p_a, token_a, headers_a = _register_user("tenant_a", "password123")
    u_b, p_b, token_b, headers_b = _register_user("tenant_b", "password123")

    board_a = client.get("/api/board", headers=headers_a).json()
    col_a_id = board_a["columns"][0]["id"]
    proj_a_id = board_a["boardId"]

    # Tenant A creates Card A
    card_a_id = client.post("/api/cards", json={"columnId": col_a_id, "title": "Secret A"}, headers=headers_a).json()["card"]["id"]

    # Tenant B attempts to read Tenant A's project board
    get_res = client.get(f"/api/board?project_id={proj_a_id}", headers=headers_b)
    assert get_res.status_code == 404

    # Tenant B attempts to update Tenant A's card
    upd_res = client.put(f"/api/cards/{card_a_id}", json={"title": "Hacked Title"}, headers=headers_b)
    assert upd_res.status_code in (403, 404)

    # Tenant B attempts to move Tenant A's card
    board_b = client.get("/api/board", headers=headers_b).json()
    col_b_id = board_b["columns"][0]["id"]
    move_res = client.patch(f"/api/cards/{card_a_id}/move", json={"columnId": col_b_id, "position": 0}, headers=headers_b)
    assert move_res.status_code in (403, 404)

    # Tenant B attempts to delete Tenant A's card
    del_res = client.delete(f"/api/cards/{card_a_id}", headers=headers_b)
    assert del_res.status_code in (403, 404)

    # Tenant B attempts to delete Tenant A's project
    del_proj_res = client.delete(f"/api/projects/{proj_a_id}", headers=headers_b)
    assert del_proj_res.status_code in (403, 404)


# 7. Authentication Source of Truth & Session Expiration
def test_7_auth_source_of_truth_and_session_expiration():
    u, p, token, headers = _register_user("session_tester", "password123")

    # 1. Valid session returns authenticated user
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["user"] == "session_tester"

    # 2. Passing fake username query param is completely ignored
    me_tampered = client.get("/api/auth/me?username=admin_impostor", headers=headers)
    assert me_tampered.status_code == 200
    assert me_tampered.json()["user"] == "session_tester"

    # 3. Revoked token returns 401
    client.post("/api/auth/logout", headers=headers)
    me_revoked = client.get("/api/auth/me", headers=headers)
    assert me_revoked.status_code == 401
