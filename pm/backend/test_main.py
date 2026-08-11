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

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login_success():
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"] == "user"

def test_login_failure():
    response = client.post(
        "/api/auth/login",
        json={"username": "wrong", "password": "badpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_logout():
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"success": True}

def test_root_serving():
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text or "<html" in response.text

def test_get_projects_api():
    response = client.get("/api/projects?username=testuser")
    assert response.status_code == 200
    projects = response.json()
    assert isinstance(projects, list)
    assert len(projects) >= 1
    assert projects[0]["name"] == "Main Project"

def test_create_rename_delete_project_api():
    # 1. Create Project
    create_res = client.post(
        "/api/projects?username=testuser",
        json={"name": "Q4 Roadmap"}
    )
    assert create_res.status_code == 200
    new_proj = create_res.json()
    assert new_proj["name"] == "Q4 Roadmap"
    proj_id = new_proj["id"]

    # 2. Verify in projects list
    get_res = client.get("/api/projects?username=testuser")
    proj_names = [p["name"] for p in get_res.json()]
    assert "Q4 Roadmap" in proj_names

    # 3. Rename Project
    rename_res = client.put(
        f"/api/projects/{proj_id}?username=testuser",
        json={"name": "Q4 Launch Campaign"}
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["name"] == "Q4 Launch Campaign"

    # 4. Delete Project
    del_res = client.delete(f"/api/projects/{proj_id}?username=testuser")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

def test_user_project_isolation():
    # User A creates a private project
    res_a = client.post(
        "/api/projects?username=usera",
        json={"name": "User A Private"}
    )
    assert res_a.status_code == 200
    proj_a_id = res_a.json()["id"]

    # User B attempts to fetch User A's board
    get_b = client.get(f"/api/board?username=userb&project_id={proj_a_id}")
    assert get_b.status_code == 404

    # User B attempts to rename User A's project
    rename_b = client.put(
        f"/api/projects/{proj_a_id}?username=userb",
        json={"name": "Hacked Name"}
    )
    assert rename_b.status_code == 404

    # User B attempts to delete User A's project
    del_b = client.delete(f"/api/projects/{proj_a_id}?username=userb")
    assert del_b.status_code == 404


def test_activity_history_api():
    # 1. Create project
    res = client.post("/api/projects?username=testuser", json={"name": "Activity Test Project"})
    assert res.status_code == 200
    proj_id = res.json()["id"]

    # 2. Add card
    board_res = client.get(f"/api/board?username=testuser&project_id={proj_id}")
    col_id = board_res.json()["columns"][0]["id"]

    add_res = client.post(
        "/api/cards?username=testuser",
        json={"columnId": col_id, "title": "Audit Task 1", "details": "Testing activity"}
    )
    assert add_res.status_code == 200
    card_id = add_res.json()["card"]["id"]

    # 3. Update card
    up_res = client.put(f"/api/cards/{card_id}", json={"priority": "high"})
    assert up_res.status_code == 200

    # 4. Delete card
    del_res = client.delete(f"/api/cards/{card_id}")
    assert del_res.status_code == 200

    # 5. Fetch Activity Log
    act_res = client.get(f"/api/projects/{proj_id}/activity?username=testuser")
    assert act_res.status_code == 200
    activities = act_res.json()["activities"]
    assert isinstance(activities, list)
    assert len(activities) >= 4

    action_types = [a["actionType"] for a in activities]
    assert "card_deleted" in action_types
    assert "card_updated" in action_types
    assert "card_created" in action_types
    assert "project_created" in action_types

    # 6. Verify audit log immutability (POST/DELETE to activity endpoint blocked)
    post_act = client.post(f"/api/projects/{proj_id}/activity", json={"fake": "data"})
    assert post_act.status_code in (405, 404)

    del_act = client.delete(f"/api/projects/{proj_id}/activity")
    assert del_act.status_code in (405, 404)


def test_user_registration_api():
    # 1. Register new user
    res = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "securepassword123"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["user"] == "newuser"
    assert "token" in data

    # 2. Login with registered user credentials
    login_res = client.post(
        "/api/auth/login",
        json={"username": "newuser", "password": "securepassword123"}
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"] == "newuser"

    # 3. Attempt duplicate registration
    dup_res = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "anotherpassword"}
    )
    assert dup_res.status_code == 400
    assert "already taken" in dup_res.json()["detail"]

    # 4. Check /api/auth/me
    me_res = client.get("/api/auth/me?username=newuser")
    assert me_res.status_code == 200
    assert me_res.json()["user"] == "newuser"


def test_project_member_management_and_rbac():
    # 1. Owner creates a project
    create_res = client.post("/api/projects?username=team_owner", json={"name": "Team Collab Board"})
    assert create_res.status_code == 200
    proj_id = create_res.json()["id"]

    # 2. Owner invites a member as Viewer
    add_viewer = client.post(
        f"/api/projects/{proj_id}/members?username=team_owner",
        json={"username": "team_viewer", "role": "viewer"},
    )
    assert add_viewer.status_code == 200
    assert add_viewer.json()["success"] is True

    # 3. Fetch project members
    members_res = client.get(f"/api/projects/{proj_id}/members?username=team_viewer")
    assert members_res.status_code == 200
    m_data = members_res.json()
    assert len(m_data["members"]) == 2
    assert m_data["userRole"] == "viewer"

    # 4. Remove viewer
    rem_res = client.delete(f"/api/projects/{proj_id}/members/team_viewer?username=team_owner")
    assert rem_res.status_code == 200
    assert rem_res.json()["success"] is True


def test_notifications_and_due_dates_api():
    # 1. Create a notification directly or via API
    database.create_notification(
        user_id="notif_user",
        project_id="p-1",
        notif_type="system",
        title="Welcome Notification",
        message="Welcome to Drag N Drop!",
    )

    # 2. Fetch notifications
    res = client.get("/api/notifications?username=notif_user")
    assert res.status_code == 200
    data = res.json()
    assert data["unreadCount"] >= 1
    assert len(data["notifications"]) >= 1

    notif_id = data["notifications"][0]["id"]

    # 3. Mark single notification read
    read_res = client.put(f"/api/notifications/{notif_id}/read?username=notif_user")
    assert read_res.status_code == 200

    # 4. Mark all read
    read_all_res = client.post("/api/notifications/read-all?username=notif_user")
    assert read_all_res.status_code == 200




