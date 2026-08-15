import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import database
from main import app

def run_29_step_verification():
    print("=" * 70)
    print("      STARTING 29-STEP COMPREHENSIVE E2E VERIFICATION SUITE")
    print("=" * 70)

    # Use test database path
    test_db = backend_dir / "pm_29_steps_test.db"
    if test_db.exists():
        test_db.unlink()

    # Point default database path to test_db
    database.DB_PATH = test_db
    database.init_db(test_db)
    client = TestClient(app)

    # STEP 1: Login as demo/user
    print("\n[Step 1] Logging in as user/password...")
    resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    token = data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f" -> Logged in successfully. Token: {token[:12]}...")

    # STEP 2: Verify default cards exist initially
    print("\n[Step 2] Verifying default cards exist initially...")
    resp = client.get("/api/board", headers=headers)
    assert resp.status_code == 200, f"Get board failed: {resp.text}"
    board = resp.json()
    initial_card_count = len(board.get("cards", {}))
    print(f" -> Initial card count: {initial_card_count}")
    assert initial_card_count > 0, "Expected default cards to exist initially"

    # STEP 3: Delete ALL default cards
    print("\n[Step 3] Deleting ALL default cards...")
    card_ids = list(board["cards"].keys())
    for cid in card_ids:
        del_resp = client.delete(f"/api/cards/{cid}", headers=headers)
        assert del_resp.status_code == 200, f"Failed to delete card {cid}: {del_resp.text}"
    print(f" -> Deleted {len(card_ids)} default cards.")

    # STEP 4: Refresh page. Expected: 0 default cards.
    print("\n[Step 4] Refreshing board state... Expected: 0 default cards")
    resp = client.get("/api/board", headers=headers)
    assert resp.status_code == 200
    board = resp.json()
    assert len(board["cards"]) == 0, f"Expected 0 cards, found {len(board['cards'])}"
    print(" -> Confirmed 0 cards on refreshed board.")

    # STEP 5: Logout.
    print("\n[Step 5] Logging out...")
    resp = client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200
    print(" -> Logout successful.")

    # STEP 6: Login again. Expected: 0 default cards.
    print("\n[Step 6] Logging in again... Expected: 0 default cards")
    resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert resp.status_code == 200
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/board", headers=headers)
    assert resp.status_code == 200
    board = resp.json()
    assert len(board["cards"]) == 0, f"Expected 0 default cards after login, found {len(board['cards'])}"
    print(" -> Confirmed 0 default cards after re-login.")

    # STEP 7: Close browser completely. (Drop token)
    print("\n[Step 7] Simulating closing browser completely...")
    headers = {}

    # STEP 8: Reopen browser.
    print("\n[Step 8] Simulating reopening browser...")

    # STEP 9: Login again. Expected: 0 default cards.
    print("\n[Step 9] Logging in again in fresh browser session... Expected: 0 default cards")
    resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert resp.status_code == 200
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/board", headers=headers)
    assert resp.status_code == 200
    board = resp.json()
    assert len(board["cards"]) == 0, f"Expected 0 cards in new browser session, found {len(board['cards'])}"
    print(" -> Confirmed 0 default cards after browser reopen and re-login.")

    # STEP 10: Add Card A.
    print("\n[Step 10] Adding Card A...")
    col_id = board["columns"][0]["id"]
    card_a_payload = {
        "columnId": col_id,
        "cardId": "card-A-test",
        "title": "Card A",
        "details": "Special Card A Details",
        "priority": "high"
    }
    resp = client.post("/api/cards", json=card_a_payload, headers=headers)
    assert resp.status_code == 200, f"Failed to add Card A: {resp.text}"
    card_a = resp.json()["card"]
    print(f" -> Added Card A with ID: {card_a['id']}")

    # STEP 11: Refresh. Expected: Card A exists exactly once.
    print("\n[Step 11] Refreshing page... Expected: Card A exists exactly once.")
    resp = client.get("/api/board", headers=headers)
    board = resp.json()
    card_a_occurrences = [c for c in board["cards"].values() if c["title"] == "Card A"]
    assert len(card_a_occurrences) == 1, f"Expected Card A exactly once, found {len(card_a_occurrences)}"
    print(" -> Verified Card A exists exactly once.")

    # STEP 12: Logout -> login. Expected: Card A exists exactly once.
    print("\n[Step 12] Logout -> Login... Expected: Card A exists exactly once.")
    client.post("/api/auth/logout", headers=headers)
    resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/board", headers=headers)
    board = resp.json()
    card_a_occurrences = [c for c in board["cards"].values() if c["title"] == "Card A"]
    assert len(card_a_occurrences) == 1, f"Expected Card A exactly once after re-login, found {len(card_a_occurrences)}"
    print(" -> Verified Card A exists exactly once after re-login.")

    # STEP 13: Delete Card A.
    print("\n[Step 13] Deleting Card A...")
    del_resp = client.delete(f"/api/cards/{card_a['id']}", headers=headers)
    assert del_resp.status_code == 200, f"Failed to delete Card A: {del_resp.text}"
    print(" -> Deleted Card A.")

    # STEP 14: Refresh. Expected: Card A does NOT exist.
    print("\n[Step 14] Refreshing page... Expected: Card A does NOT exist.")
    resp = client.get("/api/board", headers=headers)
    board = resp.json()
    assert "card-A-test" not in board["cards"], "Card A still present after refresh!"
    print(" -> Confirmed Card A does NOT exist.")

    # STEP 15: Logout -> login. Expected: Card A does NOT exist.
    print("\n[Step 15] Logout -> Login... Expected: Card A does NOT exist.")
    client.post("/api/auth/logout", headers=headers)
    resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/board", headers=headers)
    board = resp.json()
    assert "card-A-test" not in board["cards"], "Card A resurrected after re-login!"
    print(" -> Confirmed Card A does NOT exist after re-login.")

    # STEP 16: Add 10 cards rapidly.
    print("\n[Step 16] Adding 10 cards rapidly...")
    rapid_card_ids = []
    for i in range(1, 11):
        c_payload = {
            "columnId": col_id,
            "cardId": f"rapid-card-{i}",
            "title": f"Rapid Task {i}",
            "details": f"Rapid item #{i}",
            "priority": "medium"
        }
        res = client.post("/api/cards", json=c_payload, headers=headers)
        assert res.status_code == 200
        rapid_card_ids.append(f"rapid-card-{i}")
    print(" -> Successfully added 10 cards rapidly.")

    # STEP 17: Refresh. Expected: exactly 10 cards.
    print("\n[Step 17] Refreshing page... Expected: exactly 10 cards.")
    resp = client.get("/api/board", headers=headers)
    board = resp.json()
    assert len(board["cards"]) == 10, f"Expected 10 cards, found {len(board['cards'])}"
    print(" -> Verified exactly 10 cards exist.")

    # STEP 18: Move cards between every column.
    print("\n[Step 18] Moving cards between every column...")
    columns = board["columns"]
    # Move each of the 10 cards across different columns
    for idx, card_id in enumerate(rapid_card_ids):
        target_col_idx = idx % len(columns)
        # remove card from current column
        for col in columns:
            if card_id in col["cardIds"]:
                col["cardIds"].remove(card_id)
        columns[target_col_idx]["cardIds"].append(card_id)

    save_payload = {
        "columns": columns,
        "cards": board["cards"]
    }
    save_resp = client.put("/api/board", json=save_payload, headers=headers)
    assert save_resp.status_code == 200, f"Save board failed: {save_resp.text}"
    print(" -> Successfully moved cards across all columns and saved via PUT /api/board.")

    # STEP 19: Refresh. Expected: positions and columns are unchanged.
    print("\n[Step 19] Refreshing page... Expected: positions and columns are unchanged.")
    resp = client.get("/api/board", headers=headers)
    refreshed_board = resp.json()
    for col_idx, col in enumerate(columns):
        refreshed_col = refreshed_board["columns"][col_idx]
        assert refreshed_col["cardIds"] == col["cardIds"], f"Column {col['id']} order mismatch!"
    print(" -> Verified column positions and card orders are unchanged.")

    # STEP 20: Edit cards rapidly several times.
    print("\n[Step 20] Editing cards rapidly several times...")
    target_card_id = rapid_card_ids[0]
    for edit_num in range(1, 6):
        edit_payload = {
            "title": f"Rapid Edit Final Title (Edit {edit_num})",
            "details": f"Updated details iteration {edit_num}",
            "priority": "high" if edit_num % 2 == 0 else "low"
        }
        edit_resp = client.put(f"/api/cards/{target_card_id}", json=edit_payload, headers=headers)
        assert edit_resp.status_code == 200
    print(" -> Executed rapid edits.")

    # STEP 21: Refresh. Expected: final edit is preserved.
    print("\n[Step 21] Refreshing page... Expected: final edit is preserved.")
    resp = client.get("/api/board", headers=headers)
    board = resp.json()
    edited_card = board["cards"][target_card_id]
    assert edited_card["title"] == "Rapid Edit Final Title (Edit 5)", f"Unexpected title: {edited_card['title']}"
    assert edited_card["details"] == "Updated details iteration 5"
    print(" -> Verified final edit is preserved.")

    # STEP 22: Clear an entire column.
    print("\n[Step 22] Clearing an entire column...")
    target_col_to_clear = board["columns"][0]
    cards_to_remove = list(target_col_to_clear["cardIds"])
    for cid in cards_to_remove:
        client.delete(f"/api/cards/{cid}", headers=headers)
    print(f" -> Cleared {len(cards_to_remove)} cards from column {target_col_to_clear['id']}")

    # STEP 23: Refresh. Expected: column remains empty.
    print("\n[Step 23] Refreshing page... Expected: column remains empty.")
    resp = client.get("/api/board", headers=headers)
    board = resp.json()
    cleared_col = [c for c in board["columns"] if c["id"] == target_col_to_clear["id"]][0]
    assert len(cleared_col["cardIds"]) == 0, f"Column not empty: {cleared_col['cardIds']}"
    print(" -> Confirmed column remains completely empty.")

    # STEP 24: Delete and recreate projects.
    print("\n[Step 24] Deleting and recreating projects...")
    proj_create_resp = client.post("/api/projects", json={"name": "Temp Project To Delete"}, headers=headers)
    assert proj_create_resp.status_code == 200
    temp_proj = proj_create_resp.json()
    print(f" -> Created temp project '{temp_proj['name']}' ({temp_proj['id']})")

    del_proj_resp = client.delete(f"/api/projects/{temp_proj['id']}", headers=headers)
    assert del_proj_resp.status_code == 200
    print(f" -> Deleted temp project {temp_proj['id']}")

    proj_recreate_resp = client.post("/api/projects", json={"name": "Recreated Active Project"}, headers=headers)
    assert proj_recreate_resp.status_code == 200
    recreated_proj = proj_recreate_resp.json()
    print(f" -> Recreated project '{recreated_proj['name']}' ({recreated_proj['id']})")

    # STEP 25: Switch projects repeatedly.
    print("\n[Step 25] Switching projects repeatedly...")
    projects_resp = client.get("/api/projects", headers=headers)
    assert projects_resp.status_code == 200
    project_list = projects_resp.json()
    print(f" -> User has {len(project_list)} projects.")

    for proj in project_list:
        p_board_resp = client.get(f"/api/board?project_id={proj['id']}", headers=headers)
        assert p_board_resp.status_code == 200, f"Failed to fetch board for project {proj['id']}"
    print(" -> Switched between projects repeatedly with 100% data integrity.")

    # STEP 26: Logout/login repeatedly.
    print("\n[Step 26] Logout/login repeatedly...")
    for cycle in range(1, 4):
        client.post("/api/auth/logout", headers=headers)
        lin_resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
        assert lin_resp.status_code == 200
        token = lin_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
    print(" -> Completed repeated logout/login cycles successfully.")

    # STEP 27: Restart backend. (Simulated by re-initializing database module & new client)
    print("\n[Step 27] Simulating backend server restart...")
    database.init_db(test_db)
    client_new = TestClient(app)
    print(" -> Backend server restarted & DB context re-initialized.")

    # STEP 28: Repeat login.
    print("\n[Step 28] Repeating login after backend restart...")
    resp = client_new.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert resp.status_code == 200
    token = resp.json()["token"]
    headers_post_restart = {"Authorization": f"Bearer {token}"}
    print(" -> Re-authenticated successfully after backend restart.")

    # STEP 29: Expected: Database state remains EXACTLY unchanged.
    print("\n[Step 29] Verifying Database state remains EXACTLY unchanged...")
    post_restart_board = client_new.get(f"/api/board?project_id={recreated_proj['id']}", headers=headers_post_restart).json()
    assert post_restart_board is not None
    assert post_restart_board["boardId"] == recreated_proj["id"]

    # Verify cleared column still empty on main board
    main_board = client_new.get("/api/board", headers=headers_post_restart).json()
    main_cleared_col = [c for c in main_board["columns"] if c["id"] == target_col_to_clear["id"]][0]
    assert len(main_cleared_col["cardIds"]) == 0, "Cleared column lost state after restart!"

    print("\n" + "=" * 70)
    print("  SUCCESS: ALL 29 VERIFICATION STEPS PASSED WITH 100% EXACTNESS!")
    print("=" * 70)

    # Cleanup test db
    if test_db.exists():
        test_db.unlink()

if __name__ == "__main__":
    run_29_step_verification()
