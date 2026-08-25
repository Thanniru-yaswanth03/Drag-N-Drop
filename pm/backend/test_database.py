from pathlib import Path
import pytest
import database
from fastapi.testclient import TestClient
from main import app

TEST_DB_PATH = Path(__file__).resolve().parent / "test_pm.db"


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass
    monkeypatch.setenv("DATABASE_PATH", str(TEST_DB_PATH))
    database.init_db(TEST_DB_PATH)
    yield
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass


def test_init_db_does_not_auto_seed():
    """Verify that init_db does NOT create phantom or default users."""
    conn = database.get_db_connection(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    count = cursor.fetchone()["count"]
    conn.close()
    assert count == 0


def test_register_creates_initial_project_once():
    """Verify registration creates exactly one initial project with 5 columns."""
    res = database.register_user("alice", "password123", db_path=TEST_DB_PATH)
    assert res["success"] is True
    assert res["user"] == "alice"
    assert "token" in res

    projects = database.get_projects("alice", db_path=TEST_DB_PATH)
    assert len(projects) == 1
    assert projects[0]["name"] == "Main Project"

    board = database.get_board("alice", db_path=TEST_DB_PATH, project_id=projects[0]["id"])
    assert len(board["columns"]) == 5
    assert len(board["cards"]) == 0


def test_duplicate_registration_rejected():
    """Verify registration rejects existing usernames without overwriting."""
    res1 = database.register_user("bob", "password123", db_path=TEST_DB_PATH)
    assert res1["success"] is True

    res2 = database.register_user("bob", "differentpassword", db_path=TEST_DB_PATH)
    assert res2["success"] is False
    assert "already taken" in res2["error"].lower()

    # Verify original password still works
    auth = database.authenticate_user("bob", "password123", db_path=TEST_DB_PATH)
    assert auth is not None


def test_api_board_endpoints():
    client = TestClient(app)
    import uuid
    test_username = f"apitestuser_{uuid.uuid4().hex[:8]}"

    reg = client.post("/api/auth/register", json={"username": test_username, "password": "pass1234"})
    assert reg.status_code == 200
    token = reg.json().get("token")
    auth_headers = {"Authorization": f"Bearer {token}"}

    projects_resp = client.get("/api/projects", headers=auth_headers)
    assert projects_resp.status_code == 200
    projects = projects_resp.json()
    assert len(projects) >= 1
    project_id = projects[0]["id"]

    # Test GET /api/board
    response = client.get(f"/api/board?project_id={project_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert len(data["columns"]) == 5

    # Test POST /api/cards
    backlog_col_id = data["columns"][0]["id"]
    card_resp = client.post(
        "/api/cards",
        json={
            "columnId": backlog_col_id,
            "cardId": "card-test-99",
            "title": "Test Card",
            "details": "Notes",
            "description": "Full description",
            "priority": "high",
            "dueDate": "2026-08-30",
            "tags": ["frontend", "part11"],
            "assignee": "yash",
        },
        headers=auth_headers,
    )
    assert card_resp.status_code == 200
    card_data = card_resp.json()["card"]
    assert card_data["id"] == "card-test-99"
    assert card_data["priority"] == "high"
    assert card_data["dueDate"] == "2026-08-30"
    assert card_data["tags"] == ["frontend", "part11"]
    assert card_data["assignee"] == "yash"

    # Test PUT /api/cards/{card_id}
    put_resp = client.put(
        "/api/cards/card-test-99",
        json={
            "title": "Updated Test Card",
            "priority": "low",
            "tags": ["updated"],
        },
        headers=auth_headers,
    )
    assert put_resp.status_code == 200
    updated_card = put_resp.json()["card"]
    assert updated_card["title"] == "Updated Test Card"
    assert updated_card["priority"] == "low"
    assert updated_card["tags"] == ["updated"]

    # Test DELETE /api/cards
    del_resp = client.delete("/api/cards/card-test-99", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] == "card-test-99"


def test_enhanced_task_management_db():
    reg = database.register_user("testuser", "password123", db_path=TEST_DB_PATH)
    assert reg["success"]
    projects = database.get_projects("testuser", db_path=TEST_DB_PATH)
    board = database.get_board("testuser", db_path=TEST_DB_PATH, project_id=projects[0]["id"])
    col_id = board["columns"][0]["id"]

    added = database.add_card(
        user_id="testuser",
        column_id=col_id,
        card_id="card-part11-1",
        title="Part 11 Task",
        details="Detail text",
        description="Description text",
        priority="high",
        due_date="2026-09-01",
        tags=["core", "task"],
        assignee="batman",
        db_path=TEST_DB_PATH,
    )
    assert added["id"] == "card-part11-1"
    assert added["priority"] == "high"
    assert added["dueDate"] == "2026-09-01"
    assert added["tags"] == ["core", "task"]
    assert added["assignee"] == "batman"
    assert added["createdAt"] is not None

    updated = database.update_card(
        card_id="card-part11-1",
        updates={"title": "Renamed Part 11 Task", "priority": "medium", "assignee": "robin"},
        user_id="testuser",
        db_path=TEST_DB_PATH,
    )
    assert updated["title"] == "Renamed Part 11 Task"
    assert updated["priority"] == "medium"
    assert updated["assignee"] == "robin"
    assert updated["updatedAt"] is not None


def test_card_persistence_across_logout_and_login():
    reg = database.register_user("persistuser", "pass1234", db_path=TEST_DB_PATH)
    assert reg["success"]
    user_name = reg["user"]
    token1 = reg["token"]

    projects = database.get_projects(user_name, db_path=TEST_DB_PATH)
    proj_id = projects[0]["id"]
    board = database.get_board(user_name, db_path=TEST_DB_PATH, project_id=proj_id)

    new_card_id = "card-persistent-100"
    col_id = board["columns"][0]["id"]
    card = database.add_card(
        user_id=user_name,
        column_id=col_id,
        card_id=new_card_id,
        title="Persistent Task Title",
        details="Task details that must survive logout",
        priority="high",
        due_date="2026-10-10",
        tags=["critical"],
        db_path=TEST_DB_PATH,
    )
    assert card["id"] == new_card_id

    # Logout
    database.revoke_session(token1, db_path=TEST_DB_PATH)
    assert database.verify_session_token(token1, db_path=TEST_DB_PATH) is None

    # Login
    auth = database.authenticate_user("persistuser", "pass1234", db_path=TEST_DB_PATH)
    assert auth is not None
    token2 = auth["token"]
    assert database.verify_session_token(token2, db_path=TEST_DB_PATH) is not None

    # Fetch board after login
    after_login_projects = database.get_projects("persistuser", db_path=TEST_DB_PATH)
    after_login_board = database.get_board("persistuser", db_path=TEST_DB_PATH, project_id=after_login_projects[0]["id"])
    assert new_card_id in after_login_board["cards"]
    assert after_login_board["cards"][new_card_id]["title"] == "Persistent Task Title"
    assert after_login_board["cards"][new_card_id]["priority"] == "high"


def test_custom_database_path_resolution(monkeypatch, tmp_path):
    custom_db = tmp_path / "custom_dir" / "test_custom.db"
    monkeypatch.setenv("DATABASE_PATH", str(custom_db))
    resolved = database.get_database_path()
    assert resolved == custom_db
