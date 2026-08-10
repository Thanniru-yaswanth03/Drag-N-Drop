from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

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
