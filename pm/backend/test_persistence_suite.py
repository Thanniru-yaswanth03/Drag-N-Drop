import unittest
import tempfile
from pathlib import Path
import database

class TestPersistenceSuite(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test_pm.db"
        database.init_db(self.db_path)
        self.username = "test_user_persistence"
        database.register_user(self.username, "password123", db_path=self.db_path)
        board = database.get_board(self.username, db_path=self.db_path)
        col_id = board["columns"][0]["id"]
        database.add_card(self.username, col_id, "card-1-test_user_persistence", "Card 1", "D1", db_path=self.db_path)
        database.add_card(self.username, col_id, "card-2-test_user_persistence", "Card 2", "D2", db_path=self.db_path)
        database.add_card(self.username, col_id, "card-3-test_user_persistence", "Card 3", "D3", db_path=self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_A_and_B_delete_single_card_and_refresh(self):
        board = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(len(board["cards"]), 3)
        self.assertIn("card-1-test_user_persistence", board["cards"])

        # Delete card-1
        database.delete_card("card-1-test_user_persistence", user_id=self.username, db_path=self.db_path)

        # GET board (simulating refresh)
        board_after = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(len(board_after["cards"]), 2)
        self.assertNotIn("card-1-test_user_persistence", board_after["cards"])

    def test_C_and_D_logout_login_and_backend_restart(self):
        # Delete card-2
        database.delete_card("card-2-test_user_persistence", user_id=self.username, db_path=self.db_path)

        # Simulate backend restart by calling init_db on the same db file and getting board
        database.init_db(self.db_path)
        board = database.get_board(self.username, db_path=self.db_path)
        self.assertNotIn("card-2-test_user_persistence", board["cards"])

    def test_E_add_new_card(self):
        board = database.get_board(self.username, db_path=self.db_path)
        col_id = board["columns"][0]["id"]
        new_id = "card-custom-100"
        
        card = database.add_card(
            user_id=self.username,
            column_id=col_id,
            card_id=new_id,
            title="Custom User Card 100",
            details="Survives restart",
            priority="high",
            tags=["test"],
            db_path=self.db_path,
        )
        self.assertIsNotNone(card)

        # Re-query
        board_after = database.get_board(self.username, db_path=self.db_path)
        self.assertIn(new_id, board_after["cards"])
        self.assertEqual(board_after["cards"][new_id]["title"], "Custom User Card 100")

    def test_F_edit_card(self):
        card_id = "card-3-test_user_persistence"
        updated = database.update_card(card_id, {"title": "Edited Title 999"}, user_id=self.username, db_path=self.db_path)
        self.assertEqual(updated["title"], "Edited Title 999")

        board_after = database.get_board(self.username, db_path=self.db_path)
        self.assertEqual(board_after["cards"][card_id]["title"], "Edited Title 999")

    def test_G_move_card(self):
        board = database.get_board(self.username, db_path=self.db_path)
        target_col_id = board["columns"][1]["id"]
        card_id = "card-3-test_user_persistence"

        database.move_card(card_id, target_col_id, position=0, user_id=self.username, db_path=self.db_path)

        board_after = database.get_board(self.username, db_path=self.db_path)
        self.assertIn(card_id, board_after["columns"][1]["cardIds"])
        self.assertNotIn(card_id, board_after["columns"][0]["cardIds"])

    def test_H_and_I_delete_all_cards_empty_board_persists(self):
        board = database.get_board(self.username, db_path=self.db_path)
        for card_id in list(board["cards"].keys()):
            database.delete_card(card_id, user_id=self.username, db_path=self.db_path)

        # GET board (simulating refresh / restart)
        database.init_db(self.db_path)
        board_after = database.get_board(self.username, db_path=self.db_path)
        
        self.assertEqual(board_after["cards"], {})
        self.assertEqual(sum(len(c["cardIds"]) for c in board_after["columns"]), 0)

if __name__ == "__main__":
    unittest.main()
