from pathlib import Path
import pytest
import database
from fastapi.testclient import TestClient
from main import app

TEST_DB_PATH = Path(__file__).resolve().parent / "test_pm.db"


@pytest.fixture(autouse=True)
def setup_test_db():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    database.init_db(TEST_DB_PATH)
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def test_init_and_seed_db():
    board_id = database.seed_default_board("testuser", TEST_DB_PATH)
    assert board_id == "board-testuser"
    board = database.get_board("testuser", TEST_DB_PATH)
    assert len(board["columns"]) == 5
    assert "card-1" in board["cards"]


def test_save_board_data():
    board = database.get_board("testuser", TEST_DB_PATH)
    board["columns"][0]["title"] = "Updated Backlog"
    updated = database.save_board("testuser", board, TEST_DB_PATH)
    assert updated["columns"][0]["title"] == "Updated Backlog"


def test_api_board_endpoints():
    client = TestClient(app)
    # Test GET /api/board
    response = client.get("/api/board?username=user")
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert len(data["columns"]) == 5

    # Test POST /api/cards
    card_resp = client.post(
        "/api/cards",
        json={"columnId": "col-backlog", "cardId": "card-test-99", "title": "Test Card", "details": "Notes"},
    )
    assert card_resp.status_code == 200
    assert card_resp.json()["card"]["id"] == "card-test-99"

    # Test DELETE /api/cards
    del_resp = client.delete("/api/cards/card-test-99")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] == "card-test-99"
