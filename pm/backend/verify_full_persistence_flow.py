import unittest
import tempfile
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import database
import main
from main import app
from fastapi.testclient import TestClient

class TestEndToEndPersistenceFlow(unittest.TestCase):
    def setUp(self):
        main.LOGIN_ATTEMPTS.clear()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "e2e_test_pm.db"
        self.orig_db_path = database.DB_PATH
        database.DB_PATH = self.db_path
        database.init_db(self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        database.DB_PATH = self.orig_db_path
        self.tmp_dir.cleanup()

    def test_full_user_registration_card_addition_deletion_and_refresh(self):
        # 1. Register a brand new user
        username = "new_user_persisted"
        password = "password123"
        reg_res = self.client.post("/api/auth/register", json={"username": username, "password": password})
        self.assertEqual(reg_res.status_code, 200, f"Registration failed: {reg_res.text}")
        token = reg_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get initial board (seeded with default cards)
        board_res = self.client.get("/api/board", headers=headers)
        self.assertEqual(board_res.status_code, 200)
        board = board_res.json()
        initial_card_count = len(board["cards"])
        self.assertGreater(initial_card_count, 0, "New user board should have initial cards")

        # 3. Add a brand new custom card
        backlog_col_id = board["columns"][0]["id"]
        add_res = self.client.post(
            "/api/cards",
            json={"columnId": backlog_col_id, "title": "Brand New Persisted Task", "details": "Flow test"},
            headers=headers
        )
        self.assertEqual(add_res.status_code, 200)
        new_card_id = add_res.json()["card"]["id"]

        # 4. Delete one default card
        default_card_id = list(board["cards"].keys())[0]
        del_res = self.client.delete(f"/api/cards/{default_card_id}", headers=headers)
        self.assertEqual(del_res.status_code, 200)

        # 5. Simulate page refresh / GET /api/board
        refreshed_board_res = self.client.get("/api/board", headers=headers)
        self.assertEqual(refreshed_board_res.status_code, 200)
        refreshed_board = refreshed_board_res.json()

        # 6. Verify deleted default card does NOT reappear
        self.assertNotIn(default_card_id, refreshed_board["cards"], "Deleted default card must NOT reappear")

        # 7. Verify brand new custom card STILL exists
        self.assertIn(new_card_id, refreshed_board["cards"], "New custom card MUST exist after refresh")
        self.assertEqual(refreshed_board["cards"][new_card_id]["title"], "Brand New Persisted Task")

        # 8. Simulate Logout & Login
        logout_res = self.client.post("/api/auth/logout", headers=headers)
        self.assertEqual(logout_res.status_code, 200)

        login_res = self.client.post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(login_res.status_code, 200)
        new_token = login_res.json()["token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # 9. Verify board after login
        after_login_res = self.client.get("/api/board", headers=new_headers)
        self.assertEqual(after_login_res.status_code, 200)
        after_login_board = after_login_res.json()

        self.assertNotIn(default_card_id, after_login_board["cards"])
        self.assertIn(new_card_id, after_login_board["cards"])

if __name__ == "__main__":
    unittest.main()
