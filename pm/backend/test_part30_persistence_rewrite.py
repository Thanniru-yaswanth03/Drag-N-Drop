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

class TestPart30PersistenceRewrite(unittest.TestCase):
    def setUp(self):
        main.LOGIN_ATTEMPTS.clear()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "part30_test_pm.db"
        self.orig_db_path = database.DB_PATH
        database.DB_PATH = self.db_path
        database.init_db(self.db_path)
        self.client = TestClient(app)

    def tearDown(self):
        database.DB_PATH = self.orig_db_path
        self.tmp_dir.cleanup()

    def _register_user(self, username="user_p30", password="password123"):
        res = self.client.post("/api/auth/register", json={"username": username, "password": password})
        self.assertEqual(res.status_code, 200, f"Registration failed: {res.text}")
        token = res.json()["token"]
        headers = {"Authorization": f"Bearer {token}", "X-Session-Token": token}
        return username, password, headers

    def test_1_delete_survives_refresh(self):
        username, password, headers = self._register_user("u1_delete_refresh")
        
        # 1. Get initial board (0 cards)
        board_res = self.client.get("/api/board", headers=headers)
        self.assertEqual(board_res.status_code, 200)
        board = board_res.json()
        self.assertEqual(len(board["cards"]), 0, "Initial board must start with 0 cards")
        
        # 2. Add card
        col_id = board["columns"][0]["id"]
        add_res = self.client.post("/api/cards", json={"columnId": col_id, "title": "Card to Delete"}, headers=headers)
        card_to_delete = add_res.json()["card"]["id"]
        
        # 3. Delete card via API
        del_res = self.client.delete(f"/api/cards/{card_to_delete}", headers=headers)
        self.assertEqual(del_res.status_code, 200)
        
        # 4. Direct DB query verification
        conn = database.get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cards WHERE id = ?", (card_to_delete,))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNone(row, "Deleted card must NOT exist in SQLite database")
        
        # 5. Re-fetch board via API (Simulating page refresh)
        refreshed_res = self.client.get("/api/board", headers=headers)
        self.assertEqual(refreshed_res.status_code, 200)
        refreshed_board = refreshed_res.json()
        self.assertNotIn(card_to_delete, refreshed_board["cards"], "Deleted card must NOT reappear after refresh")

    def test_2_delete_survives_logout_login(self):
        username, password, headers = self._register_user("u2_delete_relogin")
        
        board = self.client.get("/api/board", headers=headers).json()
        col_id = board["columns"][0]["id"]
        add_res = self.client.post("/api/cards", json={"columnId": col_id, "title": "Temp Card"}, headers=headers)
        card_to_delete = add_res.json()["card"]["id"]
        
        self.client.delete(f"/api/cards/{card_to_delete}", headers=headers)
        
        # Logout
        self.client.post("/api/auth/logout", headers=headers)
        
        # Login
        login_res = self.client.post("/api/auth/login", json={"username": username, "password": password})
        self.assertEqual(login_res.status_code, 200)
        new_token = login_res.json()["token"]
        new_headers = {"Authorization": f"Bearer {new_token}", "X-Session-Token": new_token}
        
        # Re-fetch board
        after_login_board = self.client.get("/api/board", headers=new_headers).json()
        self.assertNotIn(card_to_delete, after_login_board["cards"], "Deleted card must NOT reappear after logout/login")

    def test_3_new_card_survives_refresh(self):
        username, password, headers = self._register_user("u3_new_refresh")
        
        board = self.client.get("/api/board", headers=headers).json()
        col_id = board["columns"][0]["id"]
        
        add_res = self.client.post(
            "/api/cards",
            json={"columnId": col_id, "title": "Part 30 Persisted Task", "details": "Survives refresh"},
            headers=headers
        )
        self.assertEqual(add_res.status_code, 200)
        new_card_id = add_res.json()["card"]["id"]
        
        # Refresh
        refreshed_board = self.client.get("/api/board", headers=headers).json()
        self.assertIn(new_card_id, refreshed_board["cards"], "Newly created card MUST exist after refresh")
        self.assertEqual(refreshed_board["cards"][new_card_id]["title"], "Part 30 Persisted Task")

    def test_4_new_card_survives_logout_login(self):
        username, password, headers = self._register_user("u4_new_relogin")
        
        board = self.client.get("/api/board", headers=headers).json()
        col_id = board["columns"][0]["id"]
        
        add_res = self.client.post(
            "/api/cards",
            json={"columnId": col_id, "title": "Card For Relogin", "details": "Details here"},
            headers=headers
        )
        new_card_id = add_res.json()["card"]["id"]
        
        # Logout & Relogin
        self.client.post("/api/auth/logout", headers=headers)
        login_res = self.client.post("/api/auth/login", json={"username": username, "password": password})
        new_token = login_res.json()["token"]
        new_headers = {"Authorization": f"Bearer {new_token}", "X-Session-Token": new_token}
        
        after_login_board = self.client.get("/api/board", headers=new_headers).json()
        self.assertIn(new_card_id, after_login_board["cards"], "Newly created card MUST survive logout/login")

    def test_5_empty_project_stays_empty(self):
        username, password, headers = self._register_user("u5_empty_board")
        
        board = self.client.get("/api/board", headers=headers).json()
        card_ids = list(board["cards"].keys())
        
        # Delete EVERY card
        for cid in card_ids:
            self.client.delete(f"/api/cards/{cid}", headers=headers)
            
        # Re-fetch board (Refresh 1)
        empty_board_1 = self.client.get("/api/board", headers=headers).json()
        self.assertEqual(len(empty_board_1["cards"]), 0, "Board cards count MUST be 0")
        
        # Logout & Login
        self.client.post("/api/auth/logout", headers=headers)
        login_res = self.client.post("/api/auth/login", json={"username": username, "password": password})
        new_token = login_res.json()["token"]
        new_headers = {"Authorization": f"Bearer {new_token}", "X-Session-Token": new_token}
        
        # Re-fetch board after login (Refresh 2)
        empty_board_2 = self.client.get("/api/board", headers=new_headers).json()
        self.assertEqual(len(empty_board_2["cards"]), 0, "Empty board MUST remain empty (0 cards) after re-login. Default cards MUST NOT reappear!")

    def test_6_project_isolation(self):
        username, password, headers = self._register_user("u6_proj_iso")
        
        # Fetch initial Project A
        projs = self.client.get("/api/projects", headers=headers).json()
        proj_a_id = projs[0]["id"]
        
        # Create Project B
        create_res = self.client.post("/api/projects", json={"name": "Project B"}, headers=headers)
        self.assertEqual(create_res.status_code, 200)
        proj_b_id = create_res.json()["id"]
        
        # Add Card B to Project B
        board_b = self.client.get(f"/api/board?project_id={proj_b_id}", headers=headers).json()
        col_b_id = board_b["columns"][0]["id"]
        
        add_b_res = self.client.post(
            f"/api/cards?project_id={proj_b_id}",
            json={"columnId": col_b_id, "title": "Card Exclusively in Project B", "details": "B"},
            headers=headers
        )
        card_b_id = add_b_res.json()["card"]["id"]
        
        # Fetch Project A board -> Verify Card B is NOT in Project A
        board_a = self.client.get(f"/api/board?project_id={proj_a_id}", headers=headers).json()
        self.assertNotIn(card_b_id, board_a["cards"], "Project B card MUST NOT leak into Project A")
        
        # Fetch Project B board -> Verify Card B is in Project B
        board_b_check = self.client.get(f"/api/board?project_id={proj_b_id}", headers=headers).json()
        self.assertIn(card_b_id, board_b_check["cards"], "Project B card MUST exist in Project B")

    def test_7_multi_mutation_survival(self):
        username, password, headers = self._register_user("u7_multi_mutation")
        
        board = self.client.get("/api/board", headers=headers).json()
        c_backlog_id = board["columns"][0]["id"]
        c_done_id = board["columns"][-1]["id"]
        
        # 1. Add Card 1
        c1_res = self.client.post("/api/cards", json={"columnId": c_backlog_id, "title": "Task One", "details": "D1"}, headers=headers)
        c1_id = c1_res.json()["card"]["id"]
        
        # 2. Add Card 2
        c2_res = self.client.post("/api/cards", json={"columnId": c_backlog_id, "title": "Task Two", "details": "D2"}, headers=headers)
        c2_id = c2_res.json()["card"]["id"]
        
        # 3. Edit Card 1
        self.client.put(f"/api/cards/{c1_id}", json={"title": "Task One Updated", "details": "New details"}, headers=headers)
        
        # 4. Delete Card 2
        self.client.delete(f"/api/cards/{c2_id}", headers=headers)
        
        # 5. Move Card 1 to Done column via PUT /api/board
        current_board = self.client.get("/api/board", headers=headers).json()
        # Find column 0 (backlog) and remove c1_id, add to column 4 (done)
        for col in current_board["columns"]:
            if c1_id in col["cardIds"]:
                col["cardIds"].remove(c1_id)
            if col["id"] == c_done_id:
                col["cardIds"].append(c1_id)
                
        self.client.put("/api/board", json=current_board, headers=headers)
        
        # 6. Logout & Login
        self.client.post("/api/auth/logout", headers=headers)
        login_res = self.client.post("/api/auth/login", json={"username": username, "password": password})
        new_token = login_res.json()["token"]
        new_headers = {"Authorization": f"Bearer {new_token}", "X-Session-Token": new_token}
        
        # 7. Verify final state
        final_board = self.client.get("/api/board", headers=new_headers).json()
        self.assertNotIn(c2_id, final_board["cards"], "Deleted Card 2 must be absent")
        self.assertIn(c1_id, final_board["cards"], "Card 1 must be present")
        self.assertEqual(final_board["cards"][c1_id]["title"], "Task One Updated")
        
        # Verify Card 1 is in Done column
        done_col = next(c for c in final_board["columns"] if c["id"] == c_done_id)
        self.assertIn(c1_id, done_col["cardIds"], "Card 1 must be in Done column")

if __name__ == "__main__":
    unittest.main()
