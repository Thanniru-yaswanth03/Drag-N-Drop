from pathlib import Path
import pytest
import database
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

TEST_DB_PATH = Path(__file__).resolve().parent / "test_pm_main.db"

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


def register_and_login(username: str, password: str = "SecurePass1234") -> dict:
    """Helper: register or login a user and return auth headers + token."""
    reg = client.post("/api/auth/register", json={"username": username, "password": password})
    if reg.status_code == 200:
        token = reg.json()["token"]
    else:
        login = client.post("/api/auth/login", json={"username": username, "password": password})
        assert login.status_code == 200, f"Login failed for {username}: {login.text}"
        token = login.json()["token"]
    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data



def test_login_success():
    # Register user first so they exist
    client.post("/api/auth/register", json={"username": "testloginuser", "password": "pass1234"})
    response = client.post(
        "/api/auth/login",
        json={"username": "testloginuser", "password": "pass1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"] == "testloginuser"


def test_login_failure():
    response = client.post(
        "/api/auth/login",
        json={"username": "wrong", "password": "badpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_logout():
    auth = register_and_login("logoutuser")
    response = client.post("/api/auth/logout", headers=auth["headers"])
    assert response.status_code == 200
    assert response.json() == {"success": True}
    # Token should now be invalid
    me = client.get("/api/auth/me", headers=auth["headers"])
    assert me.status_code == 401


def test_get_projects_api():
    auth = register_and_login("projlistuser")
    response = client.get("/api/projects", headers=auth["headers"])
    assert response.status_code == 200
    projects = response.json()
    assert isinstance(projects, list)
    assert len(projects) >= 1
    assert projects[0]["name"] == "Main Project"


def test_create_rename_delete_project_api():
    auth = register_and_login("projcruduser")

    # 1. Create Project
    create_res = client.post(
        "/api/projects",
        json={"name": "Q4 Roadmap"},
        headers=auth["headers"],
    )
    assert create_res.status_code == 200
    new_proj = create_res.json()
    assert new_proj["name"] == "Q4 Roadmap"
    proj_id = new_proj["id"]

    # 2. Verify in projects list
    get_res = client.get("/api/projects", headers=auth["headers"])
    proj_names = [p["name"] for p in get_res.json()]
    assert "Q4 Roadmap" in proj_names

    # 3. Rename Project
    rename_res = client.put(
        f"/api/projects/{proj_id}",
        json={"name": "Q4 Launch Campaign"},
        headers=auth["headers"],
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["name"] == "Q4 Launch Campaign"

    # 4. Delete Project
    del_res = client.delete(f"/api/projects/{proj_id}", headers=auth["headers"])
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_user_project_isolation():
    auth_a = register_and_login("usera_iso")
    auth_b = register_and_login("userb_iso")

    # User A creates a private project
    res_a = client.post(
        "/api/projects",
        json={"name": "User A Private"},
        headers=auth_a["headers"],
    )
    assert res_a.status_code == 200
    proj_a_id = res_a.json()["id"]

    # User B attempts to fetch User A's board — should be 404
    get_b = client.get(f"/api/board?project_id={proj_a_id}", headers=auth_b["headers"])
    assert get_b.status_code == 404

    # User B attempts to rename User A's project — should be 403
    rename_b = client.put(
        f"/api/projects/{proj_a_id}",
        json={"name": "Hacked Name"},
        headers=auth_b["headers"],
    )
    assert rename_b.status_code in (403, 404)

    # User B attempts to delete User A's project — should be 403
    del_b = client.delete(f"/api/projects/{proj_a_id}", headers=auth_b["headers"])
    assert del_b.status_code in (403, 404)


def test_activity_history_api():
    auth = register_and_login("activityuser")

    # 1. Create project
    res = client.post("/api/projects", json={"name": "Activity Test Project"}, headers=auth["headers"])
    assert res.status_code == 200
    proj_id = res.json()["id"]

    # 2. Fetch board to get column id
    board_res = client.get(f"/api/board?project_id={proj_id}", headers=auth["headers"])
    assert board_res.status_code == 200
    col_id = board_res.json()["columns"][0]["id"]

    # 3. Add card
    add_res = client.post(
        "/api/cards",
        json={"columnId": col_id, "title": "Audit Task 1", "details": "Testing activity"},
        headers=auth["headers"],
    )
    assert add_res.status_code == 200
    card_id = add_res.json()["card"]["id"]

    # 4. Update card
    up_res = client.put(f"/api/cards/{card_id}", json={"priority": "high"}, headers=auth["headers"])
    assert up_res.status_code == 200

    # 5. Delete card
    del_res = client.delete(f"/api/cards/{card_id}", headers=auth["headers"])
    assert del_res.status_code == 200

    # 6. Fetch Activity Log
    act_res = client.get(f"/api/projects/{proj_id}/activity", headers=auth["headers"])
    assert act_res.status_code == 200
    activities = act_res.json()["activities"]
    assert isinstance(activities, list)

    # 7. Verify audit log immutability
    post_act = client.post(f"/api/projects/{proj_id}/activity", json={"fake": "data"})
    assert post_act.status_code in (405, 404)

    del_act = client.delete(f"/api/projects/{proj_id}/activity")
    assert del_act.status_code in (405, 404)


def test_user_registration_api():
    # 1. Register new user
    res = client.post(
        "/api/auth/register",
        json={"username": "newuser_reg", "password": "securepassword123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["user"] == "newuser_reg"
    assert "token" in data

    # 2. Login with registered user credentials
    login_res = client.post(
        "/api/auth/login",
        json={"username": "newuser_reg", "password": "securepassword123"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"] == "newuser_reg"

    # 3. Attempt duplicate registration
    dup_res = client.post(
        "/api/auth/register",
        json={"username": "newuser_reg", "password": "anotherpassword"},
    )
    assert dup_res.status_code == 400
    assert "already taken" in dup_res.json()["detail"]

    # 4. Check /api/auth/me with valid token
    token = data["token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"] == "newuser_reg"

    # 5. /api/auth/me without token should 401
    me_no_auth = client.get("/api/auth/me")
    assert me_no_auth.status_code == 401


def test_project_member_management_and_rbac():
    auth_owner = register_and_login("team_owner_rbac")
    auth_viewer = register_and_login("team_viewer_rbac")

    # 1. Owner creates a project
    create_res = client.post(
        "/api/projects",
        json={"name": "Team Collab Board"},
        headers=auth_owner["headers"],
    )
    assert create_res.status_code == 200
    proj_id = create_res.json()["id"]

    # 2. Owner invites viewer
    add_viewer = client.post(
        f"/api/projects/{proj_id}/members",
        json={"username": "team_viewer_rbac", "role": "viewer"},
        headers=auth_owner["headers"],
    )
    assert add_viewer.status_code == 200
    assert add_viewer.json()["success"] is True

    # 3. Fetch project members as viewer
    members_res = client.get(f"/api/projects/{proj_id}/members", headers=auth_viewer["headers"])
    assert members_res.status_code == 200
    m_data = members_res.json()
    assert len(m_data["members"]) == 2
    assert m_data["userRole"] == "viewer"

    # 4. Remove viewer
    rem_res = client.delete(
        f"/api/projects/{proj_id}/members/team_viewer_rbac",
        headers=auth_owner["headers"],
    )
    assert rem_res.status_code == 200
    assert rem_res.json()["success"] is True


def test_notifications_and_due_dates_api():
    # Create user and session directly via DB layer to avoid rate limiter
    reg = database.register_user("notif_api_user_direct", "NotifPass9876", db_path=TEST_DB_PATH)
    assert reg["success"]
    token = reg["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    username = reg["user"]

    # 1. Create a notification directly in DB
    database.create_notification(
        user_id=username,
        project_id="p-1",
        notif_type="system",
        title="Welcome Notification",
        message="Welcome to Drag N Drop!",
    )

    # 2. Fetch notifications with valid auth
    res = client.get("/api/notifications", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["unreadCount"] >= 1
    assert len(data["notifications"]) >= 1

    notif_id = data["notifications"][0]["id"]

    # 3. Mark single notification read
    read_res = client.put(f"/api/notifications/{notif_id}/read", headers=auth_headers)
    assert read_res.status_code == 200

    # 4. Mark all read
    read_all_res = client.post("/api/notifications/read-all", headers=auth_headers)
    assert read_all_res.status_code == 200



def test_unauthenticated_requests_rejected():
    """All protected endpoints must return 401 without a valid token."""
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/board").status_code == 401
    assert client.post("/api/cards", json={"columnId": "x", "title": "t"}).status_code == 401
    assert client.put("/api/cards/fake-id", json={"title": "t"}).status_code == 401
    assert client.delete("/api/cards/fake-id").status_code == 401
    assert client.get("/api/notifications").status_code == 401
    assert client.get("/api/auth/me").status_code == 401

