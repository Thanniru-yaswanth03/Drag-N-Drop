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

class TestAuditPersistenceFailures(unittest.TestCase):
    def setUp(self):
        main.LOGIN_ATTEMPTS.clear()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "audit_test_pm.db"
        self.orig_db_path = database.DB_PATH
        database.DB_PATH = self.db_path
        database.init_db(self.db_path)
        self.username = "audit_user"
        reg_res = database.register_user(self.username, "password123", db_path=self.db_path)
        self.token = reg_res["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.client = TestClient(app)
        
        # Seed initial test cards for audit operations
        board = database.get_board(self.username, db_path=self.db_path)
        col_id = board["columns"][0]["id"]
        database.add_card(self.username, col_id, "card-1", "Initial Card 1", "Details 1", db_path=self.db_path)
        database.add_card(self.username, col_id, "card-2", "Initial Card 2", "Details 2", db_path=self.db_path)

    def tearDown(self):
        database.DB_PATH = self.orig_db_path
        self.tmp_dir.cleanup()

    def test_A_delete_single_default_card_and_refresh(self):
        # 1. Load default board
        board = database.get_board(self.username, db_path=self.db_path)
        self.assertGreater(len(board["cards"]), 0, "Default board should have cards")
        first_card_id = list(board["cards"].keys())[0]

        # 2. Delete one default card via API
        del_resp = self.client.delete(f"/api/cards/{first_card_id}", headers=self.headers)
        self.assertEqual(del_resp.status_code, 200)

        # 3. Refresh (get board again)
        refreshed_board = database.get_board(self.username, db_path=self.db_path)
        self.assertNotIn(first_card_id, refreshed_board["cards"])

    def test_B_delete_all_default_cards_and_verify_zero_cards_permanently(self):
        # 1. Delete every default card
        board = database.get_board(self.username, db_path=self.db_path)
        for cid in list(board["cards"].keys()):
            self.client.delete(f"/api/cards/{cid}", headers=self.headers)

        # 2. Refresh #1 -> Verify zero cards
        b1 = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(len(b1["cards"]), 0)

        # 3. Refresh #2 -> Verify board still contains zero cards
        b2 = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(len(b2["cards"]), 0)

        # 4. Re-init DB / simulate restart -> Verify zero cards
        database.init_db(self.db_path)
        b3 = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(len(b3["cards"]), 0)

    def test_C_add_new_card_and_refresh(self):
        board = database.get_board(self.username, db_path=self.db_path)
        col_id = board["columns"][0]["id"]
        res = self.client.post(
            "/api/cards",
            json={"columnId": col_id, "title": "New Test Card", "details": "Testing addition"},
            headers=self.headers
        )
        self.assertEqual(res.status_code, 200)
        card_id = res.json()["card"]["id"]

        # Refresh
        refreshed = database.get_board(self.username, db_path=self.db_path)
        self.assertIn(card_id, refreshed["cards"])
        self.assertEqual(refreshed["cards"][card_id]["title"], "New Test Card")

    def test_D_edit_card_modifications_remain(self):
        board = database.get_board(self.username, db_path=self.db_path)
        card_id = list(board["cards"].keys())[0]

        res = self.client.put(
            f"/api/cards/{card_id}",
            json={"title": "Updated Title ABC", "details": "Updated Details XYZ", "priority": "high"},
            headers=self.headers
        )
        self.assertEqual(res.status_code, 200)

        # Refresh
        refreshed = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(refreshed["cards"][card_id]["title"], "Updated Title ABC")
        self.assertEqual(refreshed["cards"][card_id]["priority"], "high")

    def test_E_move_card_to_another_column(self):
        board = database.get_board(self.username, db_path=self.db_path)
        source_col = board["columns"][0]
        target_col = board["columns"][1]
        card_id = source_col["cardIds"][0]

        source_col["cardIds"].remove(card_id)
        target_col["cardIds"].append(card_id)

        save_res = self.client.put("/api/board", json=board, headers=self.headers)
        self.assertEqual(save_res.status_code, 200)

        # Refresh
        refreshed = database.get_board(self.username, db_path=self.db_path)
        self.assertIn(card_id, refreshed["columns"][1]["cardIds"])
        self.assertNotIn(card_id, refreshed["columns"][0]["cardIds"])

    def test_F_delete_default_and_add_new_card(self):
        # 1. Delete all default cards
        board = database.get_board(self.username, db_path=self.db_path)
        for cid in list(board["cards"].keys()):
            self.client.delete(f"/api/cards/{cid}", headers=self.headers)

        # 2. Add brand new card
        col_id = board["columns"][0]["id"]
        res = self.client.post(
            "/api/cards",
            json={"columnId": col_id, "title": "Sole Card", "details": "Only this exists"},
            headers=self.headers
        )
        new_card_id = res.json()["card"]["id"]

        # 3. Refresh -> verify ONLY new card exists
        refreshed = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(len(refreshed["cards"]), 1)
        self.assertIn(new_card_id, refreshed["cards"])

    def test_G_clear_column_remains_empty(self):
        board = database.get_board(self.username, db_path=self.db_path)
        col_0 = board["columns"][0]
        for cid in list(col_0["cardIds"]):
            self.client.delete(f"/api/cards/{cid}", headers=self.headers)

        # Refresh
        refreshed = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(len(refreshed["columns"][0]["cardIds"]), 0)

    def test_H_empty_board_persistence(self):
        board = database.get_board(self.username, db_path=self.db_path)
        for cid in list(board["cards"].keys()):
            self.client.delete(f"/api/cards/{cid}", headers=self.headers)

        # Refresh multiple times
        for _ in range(3):
            b = database.get_board(self.username, db_path=self.db_path)
            self.assertEqual(len(b["cards"]), 0)

    def test_I_stale_localstorage_vs_db_single_source_of_truth(self):
        # Delete card-1 from backend DB
        board = database.get_board(self.username, db_path=self.db_path)
        database.delete_card("card-1", user_id=self.username, db_path=self.db_path)

        # Query backend directly to simulate frontend fetchBoard
        db_board = database.get_board(self.username, db_path=self.db_path)
        self.assertNotIn("card-1", db_board["cards"])

    def test_J_backend_auth_error_handling(self):
        # Invalid credentials must return 401 and NOT create fake project/board
        res = self.client.post("/api/auth/login", json={"username": "nonexistent", "password": "wrongpassword"})
        self.assertEqual(res.status_code, 401)

if __name__ == "__main__":
    unittest.main()
