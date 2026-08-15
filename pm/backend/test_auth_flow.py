import pytest
from fastapi.testclient import TestClient
from main import app
import database

client = TestClient(app)

def test_full_auth_flow_and_session_lifecycle(tmp_path):
    db_file = tmp_path / "test_auth.db"
    orig_db = database.DB_PATH
    database.DB_PATH = db_file
    database.init_db(db_file)
    try:
        # 1. Register a new user
        reg_resp = client.post("/api/auth/register", json={"username": "NewUser1", "password": "securepassword123"})
        assert reg_resp.status_code == 200
        reg_data = reg_resp.json()
        assert reg_data["success"] is True
        assert reg_data["user"] == "newuser1"
        token1 = reg_data["token"]
        assert token1.startswith("sess-")

        # 2. Verify /api/auth/me with Bearer token
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert me_resp.status_code == 200
        assert me_resp.json() == {"user": "newuser1", "authenticated": True}

        # 3. Verify case-insensitive login
        login_resp = client.post("/api/auth/login", json={"username": "NEWUSER1", "password": "securepassword123"})
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert login_data["success"] is True
        assert login_data["user"] == "newuser1"

        # 4. Verify duplicate registration rejected
        dup_resp = client.post("/api/auth/register", json={"username": "newuser1", "password": "anotherpassword"})
        assert dup_resp.status_code == 400
        assert "already taken" in dup_resp.json()["detail"].lower()

        # 5. Verify invalid login password
        bad_login = client.post("/api/auth/login", json={"username": "newuser1", "password": "wrongpassword"})
        assert bad_login.status_code == 401

        # 6. Verify logout revokes token
        logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token1}"})
        assert logout_resp.status_code == 200

        # 7. Revoked token is rejected on /api/auth/me
        unauth_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert unauth_resp.status_code == 401
    finally:
        database.DB_PATH = orig_db
