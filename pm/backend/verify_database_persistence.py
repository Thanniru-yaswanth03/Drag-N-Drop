import sys
from pathlib import Path
import sqlite3

# Ensure pm/backend is on path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import database

def test_database_persistence():
    print("--- STARTING DATABASE PERSISTENCE VERIFICATION ---")
    db_path = backend_dir / "pm_test_verification.db"
    if db_path.exists():
        db_path.unlink()

    # 1. Initialize DB
    database.init_db(db_path)
    print("[OK] Initialized SQLite database at:", db_path)

    # 2. Create User Alpha
    res_a = database.register_user("user_alpha", "password123", db_path=db_path)
    assert res_a["success"], "User Alpha registration failed"
    token_a = res_a["token"]
    user_a = res_a["user"]
    print(f"[OK] Registered User Alpha ({user_a}), token: {token_a}")

    # 3. Create User Beta
    res_b = database.register_user("user_beta", "password123", db_path=db_path)
    assert res_b["success"], "User Beta registration failed"
    token_b = res_b["token"]
    user_b = res_b["user"]
    print(f"[OK] Registered User Beta ({user_b}), token: {token_b}")

    # 4. Fetch initial board for User Alpha
    board_a = database.get_board(user_a, db_path=db_path)
    print("Initial User Alpha board card count:", len(board_a["cards"]))

    # 5. Add custom card for User Alpha
    col_backlog = board_a["columns"][0]["id"]
    new_card = database.add_card(
        user_id=user_a,
        column_id=col_backlog,
        card_id="card-alpha-special",
        title="Alpha Task 1",
        details="Critical work for Alpha",
        db_path=db_path
    )
    print("[OK] Added card to User Alpha board:", new_card["id"])

    # Verify directly via SQL query
    conn = database.get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM cards WHERE id = ?", ("card-alpha-special",))
    sql_card = cursor.fetchone()
    assert sql_card is not None and sql_card["title"] == "Alpha Task 1", "Card not found in SQLite table!"
    print("[OK] Verified card-alpha-special directly in SQLite 'cards' table!")

    # 6. Delete a card for User Alpha
    deleted_ok = database.delete_card("card-alpha-special", user_id=user_a, db_path=db_path)
    assert deleted_ok, "Card deletion failed"
    print("[OK] Deleted card-alpha-special from User Alpha board")

    # Verify deletion directly via SQL query
    cursor.execute("SELECT id FROM cards WHERE id = ?", ("card-alpha-special",))
    sql_deleted = cursor.fetchone()
    assert sql_deleted is None, "Deleted card still exists in SQLite table!"
    print("[OK] Confirmed card-alpha-special is GONE from SQLite 'cards' table!")

    # 7. Check User Isolation (User Beta board should not see User Alpha data)
    board_b = database.get_board(user_b, db_path=db_path)
    assert "card-alpha-special" not in board_b["cards"], "User Beta saw User Alpha card!"
    print("[OK] Confirmed User A and User B data are strictly isolated!")

    # 8. Re-login simulation (revoke session, authenticate again, fetch board)
    database.revoke_session(token_a, db_path=db_path)
    auth_a = database.authenticate_user("user_alpha", "password123", db_path=db_path)
    assert auth_a is not None, "Re-authentication failed"
    print("[OK] User Alpha re-authenticated with new session token:", auth_a["token"])

    fresh_board_a = database.get_board(user_a, db_path=db_path)
    assert "card-alpha-special" not in fresh_board_a["cards"], "Deleted card resurrected after re-login!"
    print("[OK] Verified fresh database fetch after re-login contains NO resurrected cards!")

    conn.close()
    if db_path.exists():
        db_path.unlink()
    print("--- ALL PERSISTENCE VERIFICATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    test_database_persistence()
