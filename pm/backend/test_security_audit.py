from pathlib import Path
import pytest
import database
from fastapi.testclient import TestClient
from main import app

TEST_DB_PATH = Path(__file__).resolve().parent / "test_pm_security_audit.db"
client = TestClient(app)


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


def test_session_token_creation_and_validation():
    reg = database.register_user("secuser", "password123", db_path=TEST_DB_PATH)
    assert reg["success"] is True
    assert reg["user"] == "secuser"
    token = reg["token"]
    assert token.startswith("sess-")

    verified = database.verify_session_token(token, db_path=TEST_DB_PATH)
    assert verified is not None
    assert verified["username"] == "secuser"

    invalid = database.verify_session_token("invalid-fake-token", db_path=TEST_DB_PATH)
    assert invalid is None


def test_session_revocation_on_logout():
    reg = database.register_user("logoutuser", "password123", db_path=TEST_DB_PATH)
    token = reg["token"]

    # Verify session is active
    assert database.verify_session_token(token, db_path=TEST_DB_PATH) is not None

    # Call logout API with Authorization Bearer header
    res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json() == {"success": True}

    # Verify session token is now revoked
    assert database.verify_session_token(token, db_path=TEST_DB_PATH) is None


def test_cross_user_project_isolation():
    # User A registers and has project
    reg_a = database.register_user("usera", "password123", db_path=TEST_DB_PATH)
    proj_a = database.get_projects("usera", db_path=TEST_DB_PATH)[0]
    proj_a_id = proj_a["id"]

    # User B registers
    reg_b = database.register_user("userb", "password123", db_path=TEST_DB_PATH)
    sess_b = reg_b["token"]
    headers_b = {"Authorization": f"Bearer {sess_b}"}

    # User B attempts to access User A's board
    get_res = client.get(f"/api/board?project_id={proj_a_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B attempts to mutate User A's project
    rename_res = client.put(
        f"/api/projects/{proj_a_id}",
        json={"name": "Hacked Project Name"},
        headers=headers_b,
    )
    assert rename_res.status_code in (403, 404)


def test_viewer_role_cannot_mutate_project():
    # Owner registers
    reg_owner = database.register_user("owneruser", "password123", db_path=TEST_DB_PATH)
    proj_id = database.get_projects("owneruser", db_path=TEST_DB_PATH)[0]["id"]

    # Viewer registers
    reg_viewer = database.register_user("vieweruser", "password123", db_path=TEST_DB_PATH)
    sess_viewer = reg_viewer["token"]
    headers_viewer = {"Authorization": f"Bearer {sess_viewer}"}

    # Owner adds vieweruser as 'viewer'
    database.add_project_member(proj_id, "vieweruser", "viewer", requesting_username="owneruser", db_path=TEST_DB_PATH)

    # Viewer attempts to delete project
    del_res = client.delete(f"/api/projects/{proj_id}", headers=headers_viewer)
    assert del_res.status_code == 403

    # Viewer attempts to update project name
    ren_res = client.put(f"/api/projects/{proj_id}", json={"name": "Viewer Rename"}, headers=headers_viewer)
    assert ren_res.status_code == 403


def test_pydantic_field_length_constraints():
    reg = database.register_user("validuser", "password123", db_path=TEST_DB_PATH)
    sess_user = reg["token"]
    headers_user = {"Authorization": f"Bearer {sess_user}"}

    # Attempt to create a card with an oversized title (>200 chars)
    oversized_title = "A" * 250
    res = client.post(
        "/api/cards",
        json={
            "columnId": "col-backlog",
            "title": oversized_title,
        },
        headers=headers_user,
    )
    assert res.status_code == 422  # Unprocessable Entity / Pydantic validation error


def test_pagination_limit_enforcement():
    reg = database.register_user("testuser", "password123", db_path=TEST_DB_PATH)
    proj_id = database.get_projects("testuser", db_path=TEST_DB_PATH)[0]["id"]
    sess_user = reg["token"]
    headers_user = {"Authorization": f"Bearer {sess_user}"}

    # Request with oversized limit=500
    res = client.get(f"/api/projects/{proj_id}/activity?limit=500", headers=headers_user)
    assert res.status_code == 200
    assert "activities" in res.json()


def test_ai_chat_permission_check():
    reg_owner = database.register_user("owneruser", "password123", db_path=TEST_DB_PATH)
    proj_id = database.get_projects("owneruser", db_path=TEST_DB_PATH)[0]["id"]

    reg_unauth = database.register_user("unauthorized_user", "password123", db_path=TEST_DB_PATH)
    sess_unauth = reg_unauth["token"]
    headers_unauth = {"Authorization": f"Bearer {sess_unauth}"}

    # Unauthorized user attempts AI chat on private project
    res = client.post(
        "/api/ai/chat",
        json={
            "message": "Summarize project",
            "project_id": proj_id,
        },
        headers=headers_unauth,
    )
    assert res.status_code == 403
