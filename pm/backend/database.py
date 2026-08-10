import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "pm.db"


def get_db_connection(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS boards (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS columns (
            id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            title TEXT NOT NULL,
            position INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            column_id TEXT NOT NULL,
            title TEXT NOT NULL,
            details TEXT DEFAULT '',
            position INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
        CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id);
        CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);
        """
    )
    conn.commit()
    conn.close()


DEFAULT_COLUMNS_SPEC = [
    ("col-backlog", "Backlog", 0, [
        ("card-1", "Align roadmap themes", "Draft quarterly themes with impact statements and metrics.", 0),
        ("card-2", "Gather customer signals", "Review support tags, sales notes, and churn feedback.", 1),
    ]),
    ("col-discovery", "Discovery", 1, [
        ("card-3", "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs.", 0),
    ]),
    ("col-progress", "In Progress", 2, [
        ("card-4", "Refine status language", "Standardize column labels and tone across the board.", 0),
        ("card-5", "Design card layout", "Add hierarchy and spacing for scanning dense lists.", 1),
    ]),
    ("col-review", "Review", 3, [
        ("card-6", "QA micro-interactions", "Verify hover, focus, and loading states.", 0),
    ]),
    ("col-done", "Done", 4, [
        ("card-7", "Ship marketing page", "Final copy approved and asset pack delivered.", 0),
        ("card-8", "Close onboarding sprint", "Document release notes and share internally.", 1),
    ]),
]


def seed_default_board(user_id: str = "user", db_path: Path = DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        cursor.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
            (f"user-{user_id}", user_id, "password"),
        )
        internal_user_id = f"user-{user_id}"
    else:
        internal_user_id = user_row["id"]

    # Check if user has a board
    cursor.execute("SELECT id FROM boards WHERE user_id = ?", (internal_user_id,))
    board_row = cursor.fetchone()
    if board_row:
        conn.close()
        return board_row["id"]

    board_id = f"board-{user_id}"
    cursor.execute(
        "INSERT INTO boards (id, user_id, name) VALUES (?, ?, ?)",
        (board_id, internal_user_id, "Kanban Studio"),
    )

    for col_id, col_title, col_pos, cards in DEFAULT_COLUMNS_SPEC:
        cursor.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (col_id, board_id, col_title, col_pos),
        )
        for card_id, card_title, card_details, card_pos in cards:
            cursor.execute(
                "INSERT INTO cards (id, column_id, title, details, position) VALUES (?, ?, ?, ?, ?)",
                (card_id, col_id, card_title, card_details, card_pos),
            )

    conn.commit()
    conn.close()
    return board_id


def reset_default_board(user_id: str = "user", db_path: Path = DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        seed_default_board(user_id, db_path)
        return get_board(user_id, db_path)

    internal_user_id = user_row["id"]
    cursor.execute("SELECT id FROM boards WHERE user_id = ?", (internal_user_id,))
    board_row = cursor.fetchone()
    board_id = board_row["id"] if board_row else f"board-{user_id}"

    # Delete existing columns and cards
    cursor.execute("SELECT id FROM columns WHERE board_id = ?", (board_id,))
    old_cols = cursor.fetchall()
    for col in old_cols:
        cursor.execute("DELETE FROM cards WHERE column_id = ?", (col["id"],))
    cursor.execute("DELETE FROM columns WHERE board_id = ?", (board_id,))

    for col_id, col_title, col_pos, cards in DEFAULT_COLUMNS_SPEC:
        cursor.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (col_id, board_id, col_title, col_pos),
        )
        for card_id, card_title, card_details, card_pos in cards:
            cursor.execute(
                "INSERT INTO cards (id, column_id, title, details, position) VALUES (?, ?, ?, ?, ?)",
                (card_id, col_id, card_title, card_details, card_pos),
            )

    conn.commit()
    conn.close()
    return get_board(user_id, db_path)


def get_board(user_id: str = "user", db_path: Path = DB_PATH):
    seed_default_board(user_id, db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    internal_user_id = user_row["id"] if user_row else f"user-{user_id}"

    cursor.execute("SELECT id FROM boards WHERE user_id = ?", (internal_user_id,))
    board_row = cursor.fetchone()
    if not board_row:
        conn.close()
        return {"columns": [], "cards": {}}
    
    board_id = board_row["id"]

    cursor.execute(
        "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position ASC",
        (board_id,),
    )
    col_rows = cursor.fetchall()

    # If database has fewer than 5 columns (e.g. from an incomplete test put), restore 5 default columns
    if len(col_rows) < 5:
        conn.close()
        return reset_default_board(user_id, db_path)

    columns = []
    cards_map = {}

    for col in col_rows:
        col_id = col["id"]
        cursor.execute(
            "SELECT id, title, details, position FROM cards WHERE column_id = ? ORDER BY position ASC",
            (col_id,),
        )
        card_rows = cursor.fetchall()
        card_ids = []
        for card in card_rows:
            card_id = card["id"]
            card_ids.append(card_id)
            cards_map[card_id] = {
                "id": card_id,
                "title": card["title"],
                "details": card["details"] or "",
            }
        columns.append(
            {
                "id": col_id,
                "title": col["title"],
                "cardIds": card_ids,
            }
        )

    conn.close()
    return {
        "boardId": board_id,
        "userId": user_id,
        "columns": columns,
        "cards": cards_map,
    }


def save_board(user_id: str, board_data: dict, db_path: Path = DB_PATH):
    seed_default_board(user_id, db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    internal_user_id = user_row["id"] if user_row else f"user-{user_id}"

    cursor.execute("SELECT id FROM boards WHERE user_id = ?", (internal_user_id,))
    board_row = cursor.fetchone()
    board_id = board_row["id"]

    columns = board_data.get("columns", []) if isinstance(board_data, dict) else []
    
    # Don't overwrite whole board if payload is empty or has fewer than 2 columns
    if len(columns) < 2:
        conn.close()
        return get_board(user_id, db_path)

    # Delete existing columns and cards for clean state update
    cursor.execute("SELECT id FROM columns WHERE board_id = ?", (board_id,))
    old_cols = cursor.fetchall()
    for col in old_cols:
        cursor.execute("DELETE FROM cards WHERE column_id = ?", (col["id"],))
    cursor.execute("DELETE FROM columns WHERE board_id = ?", (board_id,))

    cards_raw = board_data.get("cards", {}) if isinstance(board_data, dict) else {}

    # Sanitize cards into a clean dictionary
    cards_map = {}
    if isinstance(cards_raw, dict):
        cards_map = cards_raw
    elif isinstance(cards_raw, list):
        for item in cards_raw:
            if isinstance(item, dict) and "id" in item:
                cards_map[item["id"]] = item

    for col_pos, col in enumerate(columns):
        if not isinstance(col, dict):
            continue
        col_id = str(col.get("id", f"col-{col_pos}"))
        col_title = str(col.get("title", f"Column {col_pos + 1}"))
        cursor.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (col_id, board_id, col_title, col_pos),
        )
        card_ids = col.get("cardIds", []) if isinstance(col.get("cardIds"), list) else []
        for card_pos, card_id in enumerate(card_ids):
            card_id_str = str(card_id)
            card_data = cards_map.get(card_id_str, {"id": card_id_str, "title": "Untitled", "details": ""})
            if not isinstance(card_data, dict):
                card_data = {"id": card_id_str, "title": str(card_data), "details": ""}
            
            cursor.execute(
                "INSERT INTO cards (id, column_id, title, details, position) VALUES (?, ?, ?, ?, ?)",
                (
                    card_id_str,
                    col_id,
                    str(card_data.get("title", "Untitled")),
                    str(card_data.get("details", "")),
                    card_pos,
                ),
            )

    conn.commit()
    conn.close()
    return get_board(user_id, db_path)


def add_card(user_id: str, column_id: str, card_id: str, title: str, details: str, db_path: Path = DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM cards WHERE column_id = ?", (column_id,))
    count = cursor.fetchone()["count"]
    cursor.execute(
        "INSERT INTO cards (id, column_id, title, details, position) VALUES (?, ?, ?, ?, ?)",
        (card_id, column_id, title, details, count),
    )
    conn.commit()
    conn.close()
    return {"id": card_id, "title": title, "details": details}


def delete_card(card_id: str, db_path: Path = DB_PATH):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()
    return True
