from pathlib import Path
import pytest
import database
from fastapi.testclient import TestClient
from main import app

TEST_DB_PATH = Path(__file__).resolve().parent / "test_pm.db"


@pytest.fixture(autouse=True)
def setup_test_db():
    orig_db = database.DB_PATH
    database.DB_PATH = TEST_DB_PATH
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass
    database.init_db(TEST_DB_PATH)
    yield
    database.DB_PATH = orig_db
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass


def test_init_and_seed_db():
    board_id = database.seed_default_board("testuser", TEST_DB_PATH)
    assert board_id == "board-testuser"
    board = database.get_board("testuser", TEST_DB_PATH)
    assert len(board["columns"]) == 5
    assert len(board["cards"]) == 0


def test_save_board_data():
    database.seed_default_board("testuser", TEST_DB_PATH)
    board = database.get_board("testuser", TEST_DB_PATH)
    board["columns"][0]["title"] = "Updated Backlog"
    updated = database.save_board("testuser", board, TEST_DB_PATH)
    assert updated["columns"][0]["title"] == "Updated Backlog"


def test_api_board_endpoints():
    client = TestClient(app)
    import uuid
    # Use a unique username per test run to avoid conflicts with live DB
    test_username = f"apitestuser_{uuid.uuid4().hex[:8]}"
    # Register and login to get a session token
    reg = client.post("/api/auth/register", json={"username": test_username, "password": "pass1234"})
    if reg.status_code == 200:
        token = reg.json().get("token")
    else:
        # Fall back: already exists
        login = client.post("/api/auth/login", json={"username": test_username, "password": "pass1234"})
        assert login.status_code == 200, f"Could not auth: {login.text}"
        token = login.json().get("token")
    assert token, "Expected token from register/login"
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Seed the default board so the project exists
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

    # Test POST /api/cards with Part 11 fields
    backlog_col_id = data["columns"][0]["id"]
    card_resp = client.post(
        f"/api/cards?project_id={project_id}",
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
    database.seed_default_board("testuser", TEST_DB_PATH)
    added = database.add_card(
        user_id="testuser",
        column_id="col-backlog",
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


def test_board_with_few_columns_does_not_reset():
    database.seed_default_board("testuser", TEST_DB_PATH)
    # Create board payload with only 3 columns
    board = {
        "columns": [
            {"id": "c1", "title": "Todo", "cardIds": ["card-custom-1"]},
            {"id": "c2", "title": "Doing", "cardIds": []},
            {"id": "c3", "title": "Done", "cardIds": []},
        ],
        "cards": {
            "card-custom-1": {
                "id": "card-custom-1",
                "title": "My Custom Task",
                "details": "Important task details",
                "priority": "high",
            }
        },
    }
    saved = database.save_board("testuser", board, db_path=TEST_DB_PATH)
    assert len(saved["columns"]) == 3
    assert "card-custom-1" in saved["cards"]

    # Fetching the board again must NOT trigger reset_default_board
    fetched = database.get_board("testuser", db_path=TEST_DB_PATH)
    assert len(fetched["columns"]) == 3
    assert "card-custom-1" in fetched["cards"]
    assert fetched["cards"]["card-custom-1"]["title"] == "My Custom Task"


def test_save_board_preserves_project_id():
    database.seed_default_board("testuser", TEST_DB_PATH)
    proj = database.create_project("testuser", name="Mobile App Project", db_path=TEST_DB_PATH)
    proj_id = proj["id"]

    board_payload = {
        "columns": [
            {"id": "p-col-1", "title": "Backlog", "cardIds": ["p-card-1"]},
            {"id": "p-col-2", "title": "Done", "cardIds": []},
        ],
        "cards": {
            "p-card-1": {
                "id": "p-card-1",
                "title": "Project Task 1",
                "details": "Task for mobile app",
            }
        },
    }
    saved = database.save_board("testuser", board_payload, db_path=TEST_DB_PATH, project_id=proj_id)
    assert saved["boardId"] == proj_id
    assert len(saved["columns"]) == 2
    assert "p-card-1" in saved["cards"]

    fetched = database.get_board("testuser", db_path=TEST_DB_PATH, project_id=proj_id)
    assert fetched["boardId"] == proj_id
    assert len(fetched["columns"]) == 2
    assert "p-card-1" in fetched["cards"]


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
    board["cards"][new_card_id] = card
    board["columns"][0]["cardIds"].append(new_card_id)

    database.save_board(user_name, board, db_path=TEST_DB_PATH, project_id=proj_id)

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



