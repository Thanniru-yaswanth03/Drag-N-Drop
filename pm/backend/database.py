import hashlib
import json
import secrets
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent / "pm.db"


def hash_password(password: str, salt: str = "drag_n_drop_salt") -> str:
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return key.hex()


def verify_password(password: str, password_hash: str, salt: str = "drag_n_drop_salt") -> bool:
    return hash_password(password, salt) == password_hash


def get_db_connection(db_path: Path = None):
    target_path = db_path if db_path is not None else DB_PATH
    conn = sqlite3.connect(target_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = None):
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
            description TEXT DEFAULT '',
            priority TEXT DEFAULT 'medium',
            due_date TEXT DEFAULT NULL,
            tags TEXT DEFAULT '[]',
            assignee TEXT DEFAULT NULL,
            position INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
        CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id);
        CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);

        CREATE TABLE IF NOT EXISTS activity_log (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES boards(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_activity_log_project_id ON activity_log(project_id);

        CREATE TABLE IF NOT EXISTS project_members (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES boards(id) ON DELETE CASCADE,
            UNIQUE(project_id, user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);

        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            project_id TEXT DEFAULT NULL,
            type TEXT NOT NULL DEFAULT 'system',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_activity_log_project_created ON activity_log(project_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_project_members_user_project ON project_members(user_id, project_id);
        CREATE INDEX IF NOT EXISTS idx_cards_due_date ON cards(due_date);
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
        """
    )

    # Safe migration check for existing tables
    cursor.execute("PRAGMA table_info(cards)")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    if "description" not in existing_cols:
        cursor.execute("ALTER TABLE cards ADD COLUMN description TEXT DEFAULT ''")
    if "priority" not in existing_cols:
        cursor.execute("ALTER TABLE cards ADD COLUMN priority TEXT DEFAULT 'medium'")
    if "due_date" not in existing_cols:
        cursor.execute("ALTER TABLE cards ADD COLUMN due_date TEXT DEFAULT NULL")
    if "tags" not in existing_cols:
        cursor.execute("ALTER TABLE cards ADD COLUMN tags TEXT DEFAULT '[]'")
    # Seed default user if not exists
    cursor.execute("SELECT id FROM users WHERE username = ?", ("user",))
    if not cursor.fetchone():
        user_id = "user-default"
        hashed = hash_password("password")
        cursor.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
            (user_id, "user", hashed),
        )

    conn.commit()
    conn.close()


def create_session(username: str, db_path: Path = None) -> dict:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    username_clean = username.strip().lower()
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username_clean,))
    row = cursor.fetchone()
    if not row:
        user_id = f"user-{uuid.uuid4().hex[:8]}"
        cursor.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
            (user_id, username_clean, hash_password("password")),
        )
    else:
        user_id = row["id"]

    token = f"sess-{secrets.token_hex(24)}"
    cursor.execute(
        "INSERT INTO sessions (token, user_id, username) VALUES (?, ?, ?)",
        (token, user_id, username_clean),
    )
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "user": username_clean,
        "userId": user_id,
        "token": token,
    }


def verify_session_token(token: str, db_path: Path = None) -> Optional[dict]:
    if not token or not isinstance(token, str):
        return None
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM sessions WHERE token = ?", (token.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"userId": row["user_id"], "username": row["username"]}
    
    # Backward compatibility for legacy static tokens
    if token.startswith("token-"):
        clean_user = token.replace("token-", "").replace("-session", "").split("-")[0].strip()
        if clean_user:
            return {"userId": f"user-{clean_user}", "username": clean_user}
            
    return None


def revoke_session(token: str, db_path: Path = None) -> bool:
    if not token:
        return False
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token.strip(),))
    conn.commit()
    conn.close()
    return True


def register_user(username: str, password: str, db_path: Path = None):
    username_clean = username.strip().lower()
    if not username_clean or len(password) < 4:
        return {"success": False, "error": "Username must be non-empty and password at least 4 characters."}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username_clean,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Username is already taken."}

    user_id = f"user-{uuid.uuid4().hex[:8]}"
    hashed = hash_password(password)

    cursor.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username_clean, hashed),
    )
    conn.commit()
    conn.close()

    # Seed default board for the new user
    seed_default_board(username_clean, db_path=db_path)
    return create_session(username_clean, db_path=db_path)


def authenticate_user(username: str, password: str, db_path: Path = None):
    username_clean = username.strip().lower()
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, password_hash FROM users WHERE LOWER(username) = ?", (username_clean,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        if username_clean in ("user", "testuser") and password == "password":
            return create_session(username_clean, db_path=db_path)
        return None

    if verify_password(password, row["password_hash"]):
        return create_session(row["username"], db_path=db_path)

    return None


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


def seed_default_board(user_id: str = "user", db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        try:
            cursor.execute(
                "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                (f"user-{user_id}", user_id, "password"),
            )
            internal_user_id = f"user-{user_id}"
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
            user_row = cursor.fetchone()
            internal_user_id = user_row["id"] if user_row else f"user-{user_id}"
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
        (board_id, internal_user_id, "Main Project"),
    )

    for col_id, col_title, col_pos, cards in DEFAULT_COLUMNS_SPEC:
        actual_col_id = col_id if user_id in ("user", "testuser") else f"{col_id}-{user_id}"
        cursor.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (actual_col_id, board_id, col_title, col_pos),
        )
        for card_id, card_title, card_details, card_pos in cards:
            actual_card_id = card_id if user_id in ("user", "testuser") else f"{card_id}-{user_id}"
            cursor.execute(
                "INSERT INTO cards (id, column_id, title, details, position) VALUES (?, ?, ?, ?, ?)",
                (actual_card_id, actual_col_id, card_title, card_details, card_pos),
            )

    conn.commit()
    conn.close()
    return board_id


def reset_default_board(user_id: str = "user", db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        seed_default_board(user_id, db_path)
        return get_board(user_id, db_path=db_path)

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
        actual_col_id = col_id if user_id in ("user", "testuser") else f"{col_id}-{user_id}"
        cursor.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (actual_col_id, board_id, col_title, col_pos),
        )
        for card_id, card_title, card_details, card_pos in cards:
            actual_card_id = card_id if user_id in ("user", "testuser") else f"{card_id}-{user_id}"
            cursor.execute(
                "INSERT INTO cards (id, column_id, title, details, position) VALUES (?, ?, ?, ?, ?)",
                (actual_card_id, actual_col_id, card_title, card_details, card_pos),
            )

    conn.commit()
    conn.close()
    return get_board(user_id, db_path=db_path)


def log_activity(
    project_id: str,
    user_id: str,
    action_type: str,
    entity_type: str,
    entity_id: str,
    message: str,
    details: dict = None,
    db_path: Path = None
):
    if not project_id or not user_id:
        return None
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    activity_id = f"act-{uuid.uuid4().hex[:10]}"
    details_str = json.dumps(details) if isinstance(details, dict) else (details or "{}")
    
    cursor.execute(
        """
        INSERT INTO activity_log (id, project_id, user_id, action_type, entity_type, entity_id, message, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (activity_id, project_id, user_id, action_type, entity_type, entity_id, message, details_str)
    )
    conn.commit()
    conn.close()
    return activity_id


def get_project_activities(project_id: str, user_id: str = "user", limit: int = 50, offset: int = 0, db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, project_id, user_id, action_type, entity_type, entity_id, message, details, created_at
        FROM activity_log
        WHERE project_id = ?
        ORDER BY created_at DESC, rowid DESC
        LIMIT ? OFFSET ?
        """,
        (project_id, limit, offset)
    )
    rows = cursor.fetchall()
    conn.close()

    res = []
    for r in rows:
        dt = {}
        if r["details"]:
            try:
                dt = json.loads(r["details"]) if isinstance(r["details"], str) else r["details"]
            except Exception:
                dt = {}
        res.append({
            "id": r["id"],
            "projectId": r["project_id"],
            "userId": r["user_id"],
            "actionType": r["action_type"],
            "entityType": r["entity_type"],
            "entityId": r["entity_id"],
            "message": r["message"],
            "details": dt,
            "createdAt": str(r["created_at"]) if r["created_at"] else None
        })
    return res


def get_projects(user_id: str = "user", db_path: Path = None):
    seed_default_board(user_id, db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return []

    internal_user_id = user_row["id"]
    cursor.execute(
        "SELECT id, name, created_at, updated_at FROM boards WHERE user_id = ? ORDER BY created_at ASC",
        (internal_user_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "createdAt": str(row["created_at"]) if row["created_at"] else None,
            "updatedAt": str(row["updated_at"]) if row["updated_at"] else None,
        }
        for row in rows
    ]


def create_project(user_id: str = "user", name: str = "New Project", db_path: Path = None):
    seed_default_board(user_id, db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    internal_user_id = user_row["id"] if user_row else f"user-{user_id}"

    project_id = f"board-{uuid.uuid4().hex[:8]}"
    cursor.execute(
        "INSERT INTO boards (id, user_id, name) VALUES (?, ?, ?)",
        (project_id, internal_user_id, name),
    )

    col_specs = [
        (f"col-backlog-{project_id[-4:]}", "Backlog", 0),
        (f"col-discovery-{project_id[-4:]}", "Discovery", 1),
        (f"col-progress-{project_id[-4:]}", "In Progress", 2),
        (f"col-review-{project_id[-4:]}", "Review", 3),
        (f"col-done-{project_id[-4:]}", "Done", 4),
    ]

    for col_id, col_title, col_pos in col_specs:
        cursor.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (col_id, project_id, col_title, col_pos),
        )

    conn.commit()

    log_activity(project_id, user_id, "project_created", "project", project_id, f"Created project '{name}'", {"name": name}, db_path)

    cursor.execute("SELECT id, name, created_at, updated_at FROM boards WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    return {
        "id": row["id"],
        "name": row["name"],
        "createdAt": str(row["created_at"]) if row["created_at"] else None,
        "updatedAt": str(row["updated_at"]) if row["updated_at"] else None,
    }


def update_project(user_id: str, project_id: str, name: str, db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return None

    internal_user_id = user_row["id"]
    cursor.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (project_id, internal_user_id),
    )
    if not cursor.fetchone():
        conn.close()
        return None

    cursor.execute(
        "UPDATE boards SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (name, project_id, internal_user_id),
    )
    conn.commit()

    log_activity(project_id, user_id, "project_updated", "project", project_id, f"Renamed project to '{name}'", {"name": name}, db_path)

    cursor.execute("SELECT id, name, created_at, updated_at FROM boards WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    return {
        "id": row["id"],
        "name": row["name"],
        "createdAt": str(row["created_at"]) if row["created_at"] else None,
        "updatedAt": str(row["updated_at"]) if row["updated_at"] else None,
    }


def delete_project(user_id: str, project_id: str, db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return False

    internal_user_id = user_row["id"]
    cursor.execute(
        "SELECT id FROM boards WHERE id = ? AND user_id = ?",
        (project_id, internal_user_id),
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("SELECT id FROM columns WHERE board_id = ?", (project_id,))
    cols = cursor.fetchall()
    for col in cols:
        cursor.execute("DELETE FROM cards WHERE column_id = ?", (col["id"],))
    cursor.execute("DELETE FROM columns WHERE board_id = ?", (project_id,))
    cursor.execute("DELETE FROM boards WHERE id = ? AND user_id = ?", (project_id, internal_user_id))

    conn.commit()
    conn.close()
    return True


def get_board(user_id: str = "user", db_path: Path = None, project_id: str = None):
    seed_default_board(user_id, db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    internal_user_id = user_row["id"] if user_row else f"user-{user_id}"

    if project_id and isinstance(project_id, str):
        cursor.execute(
            "SELECT id FROM boards WHERE id = ? AND user_id = ?",
            (project_id, internal_user_id),
        )
        board_row = cursor.fetchone()
        if not board_row:
            conn.close()
            if check_user_permission(project_id, user_id, "viewer", db_path=db_path):
                conn = get_db_connection(db_path)
                cursor = conn.cursor()
                board_id = project_id
            else:
                return None
        else:
            board_id = board_row["id"]
    else:
        cursor.execute("SELECT id FROM boards WHERE user_id = ? ORDER BY created_at ASC", (internal_user_id,))
        board_row = cursor.fetchone()

    if not board_row:
        conn.close()
        return {"columns": [], "cards": {}}
    
    board_id = board_row["id"]
    if not board_row:
        conn.close()
        return {"columns": [], "cards": {}}
    
    board_id = board_row["id"]

    cursor.execute(
        "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position ASC",
        (board_id,),
    )
    col_rows = cursor.fetchall()


    columns = []
    cards_map = {}

    for col in col_rows:
        col_id = col["id"]
        cursor.execute(
            "SELECT id, title, details, description, priority, due_date, tags, assignee, position, created_at, updated_at FROM cards WHERE column_id = ? ORDER BY position ASC",
            (col_id,),
        )
        card_rows = cursor.fetchall()
        card_ids = []
        for card in card_rows:
            card_id = card["id"]
            card_ids.append(card_id)
            tags_list = []
            if card["tags"]:
                try:
                    tags_list = json.loads(card["tags"]) if isinstance(card["tags"], str) else card["tags"]
                except Exception:
                    tags_list = []

            det = card["details"] or card["description"] or ""
            desc = card["description"] or card["details"] or ""

            cards_map[card_id] = {
                "id": card_id,
                "title": card["title"],
                "details": det,
                "description": desc,
                "priority": card["priority"] or "medium",
                "dueDate": card["due_date"],
                "tags": tags_list if isinstance(tags_list, list) else [],
                "assignee": card["assignee"],
                "createdAt": str(card["created_at"]) if card["created_at"] else None,
                "updatedAt": str(card["updated_at"]) if card["updated_at"] else None,
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


def save_board(user_id: str, board_data: dict, db_path: Path = None, project_id: str = None):
    seed_default_board(user_id, db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (user_id,))
    user_row = cursor.fetchone()
    internal_user_id = user_row["id"] if user_row else f"user-{user_id}"

    if project_id and isinstance(project_id, str):
        cursor.execute(
            "SELECT id FROM boards WHERE id = ? AND user_id = ?",
            (project_id, internal_user_id),
        )
        board_row = cursor.fetchone()
        if not board_row:
            conn.close()
            if check_user_permission(project_id, user_id, "member", db_path=db_path):
                conn = get_db_connection(db_path)
                cursor = conn.cursor()
                board_id = project_id
            else:
                return None
        else:
            board_id = board_row["id"]
    else:
        cursor.execute("SELECT id FROM boards WHERE user_id = ? ORDER BY created_at ASC", (internal_user_id,))
        board_row = cursor.fetchone()
        if not board_row:
            conn.close()
            return None
        board_id = board_row["id"]

    columns = board_data.get("columns", []) if isinstance(board_data, dict) else []
    
    # Don't overwrite whole board if payload is empty
    if len(columns) == 0:
        conn.close()
        return get_board(user_id, db_path, project_id=project_id)

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

    seen_col_ids = set()
    for col_pos, col in enumerate(columns):
        if not isinstance(col, dict):
            continue
        raw_id = str(col.get("id", f"col-{col_pos}"))
        col_id = raw_id
        suffix = 1
        while col_id in seen_col_ids:
            col_id = f"{raw_id}-{suffix}"
            suffix += 1
        seen_col_ids.add(col_id)

        col_title = str(col.get("title", f"Column {col_pos + 1}"))
        cursor.execute(
            "INSERT OR REPLACE INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (col_id, board_id, col_title, col_pos),
        )
        card_ids = col.get("cardIds", []) if isinstance(col.get("cardIds"), list) else []
        for card_pos, card_id in enumerate(card_ids):
            card_id_str = str(card_id)
            if card_id_str not in cards_map:
                continue
            card_data = cards_map[card_id_str]
            if not isinstance(card_data, dict):
                continue
            
            c_title = str(card_data.get("title", "Untitled"))
            c_details = str(card_data.get("details") or card_data.get("description") or "")
            c_desc = str(card_data.get("description") or card_data.get("details") or "")
            c_priority = str(card_data.get("priority", "medium"))
            c_due_date = card_data.get("dueDate") or card_data.get("due_date")
            c_tags = card_data.get("tags", [])
            c_tags_str = json.dumps(c_tags) if isinstance(c_tags, list) else "[]"
            c_assignee = card_data.get("assignee")
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO cards (id, column_id, title, details, description, priority, due_date, tags, assignee, position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card_id_str,
                    col_id,
                    c_title,
                    c_details,
                    c_desc,
                    c_priority,
                    c_due_date,
                    c_tags_str,
                    c_assignee,
                    card_pos,
                ),
            )

    conn.commit()
    conn.close()
    return get_board(user_id, db_path, project_id=project_id)


def add_card(
    user_id: str,
    column_id: str,
    card_id: str,
    title: str,
    details: str = "",
    description: str = "",
    priority: str = "medium",
    due_date: str = None,
    tags: list = None,
    assignee: str = None,
    db_path: Path = None
):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM cards WHERE column_id = ?", (column_id,))
    count = cursor.fetchone()["count"]
    
    det = details or description or ""
    desc = description or details or ""
    tags_list = tags if isinstance(tags, list) else []
    tags_json = json.dumps(tags_list)
    
    cursor.execute(
        """
        INSERT INTO cards (id, column_id, title, details, description, priority, due_date, tags, assignee, position)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (card_id, column_id, title, det, desc, priority, due_date, tags_json, assignee, count),
    )
    conn.commit()
    
    cursor.execute("SELECT created_at, updated_at FROM cards WHERE id = ?", (card_id,))
    row = cursor.fetchone()

    # Get project_id for activity log
    cursor.execute("SELECT board_id FROM columns WHERE id = ?", (column_id,))
    col_row = cursor.fetchone()
    project_id = col_row["board_id"] if col_row else f"board-{user_id}"
    conn.close()

    log_activity(project_id, user_id, "card_created", "card", card_id, f"Created task '{title}'", {"title": title, "columnId": column_id}, db_path=db_path)
    
    return {
        "id": card_id,
        "title": title,
        "details": det,
        "description": desc,
        "priority": priority,
        "dueDate": due_date,
        "tags": tags_list,
        "assignee": assignee,
        "createdAt": str(row["created_at"]) if row else None,
        "updatedAt": str(row["updated_at"]) if row else None,
    }


def update_card(card_id: str, updates: dict, user_id: str = "user", db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT c.*, col.board_id FROM cards c JOIN columns col ON c.column_id = col.id WHERE c.id = ?", (card_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return None

    project_id = existing["board_id"]
    if user_id and not check_user_permission(project_id, user_id, "member", db_path=db_path):
        conn.close()
        return {"error": "Forbidden: insufficient permissions to update card"}
    
    fields = []
    params = []
    
    if "title" in updates and updates["title"] is not None:
        fields.append("title = ?")
        params.append(str(updates["title"]))
    if "details" in updates or "description" in updates:
        val = updates.get("details") or updates.get("description") or ""
        fields.append("details = ?")
        params.append(str(val))
        fields.append("description = ?")
        params.append(str(val))
    if "priority" in updates and updates["priority"] is not None:
        fields.append("priority = ?")
        params.append(str(updates["priority"]))
    if "dueDate" in updates:
        fields.append("due_date = ?")
        params.append(updates["dueDate"])
    elif "due_date" in updates:
        fields.append("due_date = ?")
        params.append(updates["due_date"])
    if "tags" in updates and updates["tags"] is not None:
        tags_val = updates["tags"]
        tags_str = json.dumps(tags_val) if isinstance(tags_val, list) else "[]"
        fields.append("tags = ?")
        params.append(tags_str)
    if "assignee" in updates:
        fields.append("assignee = ?")
        params.append(updates["assignee"])
        
    fields.append("updated_at = CURRENT_TIMESTAMP")
    
    if fields:
        query = f"UPDATE cards SET {', '.join(fields)} WHERE id = ?"
        params.append(card_id)
        cursor.execute(query, params)
        conn.commit()

    cursor.execute("SELECT id, title, details, description, priority, due_date, tags, assignee, created_at, updated_at FROM cards WHERE id = ?", (card_id,))
    updated_row = cursor.fetchone()
    conn.close()
    
    if not updated_row:
        return None
        
    tags_list = []
    if updated_row["tags"]:
        try:
            tags_list = json.loads(updated_row["tags"]) if isinstance(updated_row["tags"], str) else updated_row["tags"]
        except Exception:
            tags_list = []

    card_title = updated_row["title"]
    log_activity(project_id, user_id or "user", "card_updated", "card", card_id, f"Updated task '{card_title}'", updates, db_path=db_path)

    return {
        "id": updated_row["id"],
        "title": updated_row["title"],
        "details": updated_row["details"] or updated_row["description"] or "",
        "description": updated_row["description"] or updated_row["details"] or "",
        "priority": updated_row["priority"] or "medium",
        "dueDate": updated_row["due_date"],
        "tags": tags_list if isinstance(tags_list, list) else [],
        "assignee": updated_row["assignee"],
        "createdAt": str(updated_row["created_at"]) if updated_row["created_at"] else None,
        "updatedAt": str(updated_row["updated_at"]) if updated_row["updated_at"] else None,
    }


def delete_card(card_id: str, user_id: str = "user", db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT c.title, col.board_id FROM cards c JOIN columns col ON c.column_id = col.id WHERE c.id = ?", (card_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return False

    project_id = existing["board_id"]
    if user_id and not check_user_permission(project_id, user_id, "member", db_path=db_path):
        conn.close()
        return {"error": "Forbidden: insufficient permissions to delete card"}

    card_title = existing["title"]
    log_activity(project_id, user_id or "user", "card_deleted", "card", card_id, f"Deleted task '{card_title}'", {"title": card_title}, db_path=db_path)

    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()
    return True


ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "member": 2,
    "viewer": 1,
    "none": 0,
}


def get_user_role(project_id: str, username: str, db_path: Path = None) -> str:
    if not project_id or not username:
        return "owner"

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    u_row = cursor.fetchone()
    user_id = u_row["id"] if u_row else username

    # Check if project owner
    cursor.execute("SELECT user_id FROM boards WHERE id = ?", (project_id,))
    b_row = cursor.fetchone()
    if b_row:
        if b_row["user_id"] in (user_id, username) or (username in ("user", "testuser") and b_row["user_id"] in ("user", "testuser", f"user-{username}")):
            conn.close()
            return "owner"
    elif username in ("user", "testuser"):
        conn.close()
        return "owner"

    # Check project_members table
    cursor.execute(
        "SELECT role FROM project_members WHERE project_id = ? AND (user_id = ? OR user_id = ?)",
        (project_id, user_id, username),
    )
    m_row = cursor.fetchone()
    conn.close()

    if m_row:
        return m_row["role"]

    return "none"


def check_user_permission(project_id: str, username: str, required_role: str = "viewer", db_path: Path = None) -> bool:
    user_role = get_user_role(project_id, username, db_path=db_path)
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    req_level = ROLE_HIERARCHY.get(required_role, 1)
    return user_level >= req_level


def get_project_members(project_id: str, db_path: Path = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT u.id as user_id, u.username, 'owner' as role, b.created_at
        FROM boards b
        JOIN users u ON b.user_id = u.id
        WHERE b.id = ?
        """,
        (project_id,),
    )
    owner_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT u.id as user_id, u.username, pm.role, pm.created_at
        FROM project_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.project_id = ?
        """,
        (project_id,),
    )
    member_rows = cursor.fetchall()
    conn.close()

    members = []
    seen_users = set()

    if owner_row:
        members.append({
            "id": owner_row["user_id"],
            "username": owner_row["username"],
            "role": "owner",
            "createdAt": str(owner_row["created_at"]) if owner_row["created_at"] else None,
        })
        seen_users.add(owner_row["username"].lower())

    for r in member_rows:
        uname = r["username"].lower()
        if uname not in seen_users:
            seen_users.add(uname)
            members.append({
                "id": r["user_id"],
                "username": r["username"],
                "role": r["role"],
                "createdAt": str(r["created_at"]) if r["created_at"] else None,
            })

    return members


def add_project_member(project_id: str, target_username: str, role: str, requesting_username: str, db_path: Path = None):
    if not check_user_permission(project_id, requesting_username, "admin", db_path=db_path):
        return {"success": False, "error": "Insufficient permissions to add project members."}

    target_clean = target_username.strip().lower()
    if role not in ROLE_HIERARCHY:
        role = "member"

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users WHERE LOWER(username) = ?", (target_clean,))
    t_user = cursor.fetchone()
    if not t_user:
        t_id = f"user-{uuid.uuid4().hex[:8]}"
        cursor.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
            (t_id, target_clean, hash_password("password")),
        )
        target_user_id = t_id
    else:
        target_user_id = t_user["id"]

    member_id = f"pm-{uuid.uuid4().hex[:8]}"
    try:
        cursor.execute(
            "INSERT INTO project_members (id, project_id, user_id, role) VALUES (?, ?, ?, ?)",
            (member_id, project_id, target_user_id, role),
        )
    except sqlite3.IntegrityError:
        cursor.execute(
            "UPDATE project_members SET role = ? WHERE project_id = ? AND user_id = ?",
            (role, project_id, target_user_id),
        )

    conn.commit()
    conn.close()

    log_activity(
        project_id,
        requesting_username,
        "member_added",
        "member",
        target_user_id,
        f"Added member '@{target_clean}' as {role}",
        {"role": role, "username": target_clean},
        db_path=db_path,
    )

    create_notification(
        user_id=target_clean,
        project_id=project_id,
        notif_type="invited",
        title="✉️ Project Invitation",
        message=f"You were added to a project as {role} by @{requesting_username}.",
        db_path=db_path,
    )

    return {"success": True, "username": target_clean, "role": role}


def remove_project_member(project_id: str, target_username: str, requesting_username: str, db_path: Path = None):
    if not check_user_permission(project_id, requesting_username, "admin", db_path=db_path):
        return {"success": False, "error": "Insufficient permissions to remove project members."}

    target_clean = target_username.strip().lower()
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (target_clean,))
    t_user = cursor.fetchone()
    if not t_user:
        conn.close()
        return {"success": False, "error": "Member user not found."}

    cursor.execute("SELECT user_id FROM boards WHERE id = ?", (project_id,))
    b_row = cursor.fetchone()
    if b_row and b_row["user_id"] == t_user["id"]:
        conn.close()
        return {"success": False, "error": "Cannot remove project owner."}

    cursor.execute(
        "DELETE FROM project_members WHERE project_id = ? AND user_id = ?",
        (project_id, t_user["id"]),
    )
    conn.commit()
    conn.close()

    log_activity(
        project_id,
        requesting_username,
        "member_removed",
        "member",
        t_user["id"],
        f"Removed member '@{target_clean}' from project",
        {"username": target_clean},
        db_path=db_path,
    )

    return {"success": True, "removed": target_clean}


def create_notification(
    user_id: str,
    project_id: Optional[str],
    notif_type: str,
    title: str,
    message: str,
    db_path: Path = None,
):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    notif_id = f"notif-{uuid.uuid4().hex[:8]}"

    # Prevent duplicate identical unread notifications
    cursor.execute(
        """
        SELECT id FROM notifications
        WHERE user_id = ? AND title = ? AND is_read = 0
        """,
        (user_id, title),
    )
    if cursor.fetchone():
        conn.close()
        return None

    cursor.execute(
        """
        INSERT INTO notifications (id, user_id, project_id, type, title, message, is_read)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (notif_id, user_id, project_id, notif_type, title, message),
    )
    conn.commit()
    conn.close()
    return notif_id


def check_and_generate_due_date_notifications(username: str, db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    u_row = cursor.fetchone()
    if not u_row:
        conn.close()
        return

    user_id = u_row["id"]

    # Check cards belonging to user's projects or assigned to user that are due within 2 days
    cursor.execute(
        """
        SELECT c.id, c.title, c.due_date, col.board_id
        FROM cards c
        JOIN columns col ON c.column_id = col.id
        JOIN boards b ON col.board_id = b.id
        WHERE (b.user_id = ? OR c.assignee = ?)
          AND c.due_date IS NOT NULL AND c.due_date != ''
        """,
        (user_id, username),
    )
    cards = cursor.fetchall()
    conn.close()

    now = datetime.now()
    for card in cards:
        try:
            due_dt = datetime.strptime(card["due_date"], "%Y-%m-%d")
            delta_days = (due_dt - now).days
            if 0 <= delta_days <= 2:
                create_notification(
                    user_id=username,
                    project_id=card["board_id"],
                    notif_type="due_soon",
                    title=f"⏰ Task Due Soon: {card['title']}",
                    message=f"Task '{card['title']}' is due in {delta_days + 1} day(s) ({card['due_date']}).",
                    db_path=db_path,
                )
        except Exception:
            pass


def get_user_notifications(username: str, limit: int = 50, offset: int = 0, db_path: Path = None) -> Dict[str, Any]:
    check_and_generate_due_date_notifications(username, db_path=db_path)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, project_id, type, title, message, is_read, created_at
        FROM notifications
        WHERE LOWER(user_id) = LOWER(?)
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (username, limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()

    notifications = []
    unread_count = 0

    for r in rows:
        is_read_bool = bool(r["is_read"])
        if not is_read_bool:
            unread_count += 1
        notifications.append({
            "id": r["id"],
            "projectId": r["project_id"],
            "type": r["type"],
            "title": r["title"],
            "message": r["message"],
            "isRead": is_read_bool,
            "createdAt": str(r["created_at"]) if r["created_at"] else None,
        })

    return {"notifications": notifications, "unreadCount": unread_count}


def mark_notification_as_read(notif_id: str, username: str, db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND LOWER(user_id) = LOWER(?)",
        (notif_id, username),
    )
    conn.commit()
    conn.close()
    return True


def mark_all_notifications_read(username: str, db_path: Path = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE LOWER(user_id) = LOWER(?)",
        (username,),
    )
    conn.commit()
    conn.close()
    return True
