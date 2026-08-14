import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_ai_test_endpoint():
    response = client.post("/api/ai/test")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_ai_chat_endpoint_mock_addition():
    import database
    sess = database.create_session("user")["token"]
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
