import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from main import app
import database
import config

TEST_DB_PATH = Path(__file__).resolve().parent / "test_pm_ai.db"
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


def test_ai_test_endpoint():
    response = client.post("/api/ai/test")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_ai_chat_endpoint_mock_addition(monkeypatch):
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "")
    reg = database.register_user("aiuser", "password123", db_path=TEST_DB_PATH)
    sess = reg["token"]
    response = client.post(
        "/api/ai/chat",
        json={
            "message": "Add a card for QA testing to In Progress",
            "history": [],
        },
        headers={"Authorization": f"Bearer {sess}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["board_update"] is not None
    assert "columns" in data["board_update"]
