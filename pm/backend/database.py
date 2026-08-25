import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Sequence

import config

logger = logging.getLogger("drag_n_drop.database")

# Optional psycopg PostgreSQL support
try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
    HAS_PSYCOPG = True
except ImportError:
    HAS_PSYCOPG = False
    psycopg = None
    dict_row = None
    ConnectionPool = None

# Global PostgreSQL connection pools keyed by database URL
_PG_POOLS: Dict[str, Any] = {}


def get_pg_pool(database_url: str) -> Any:
    """Retrieve or initialize a thread-safe psycopg connection pool for PostgreSQL."""
    if not HAS_PSYCOPG:
        raise RuntimeError(
            "psycopg is not installed. Install psycopg[binary] and psycopg-pool for PostgreSQL support."
        )
    if database_url not in _PG_POOLS:
        # Standardize postgres:// to postgresql://
        url = database_url
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        logger.info("Initializing PostgreSQL connection pool for %s", mask_database_url(url))
        _PG_POOLS[database_url] = ConnectionPool(
            conninfo=url,
            min_size=1,
            max_size=10,
            timeout=30.0,
            open=True,
            kwargs={"row_factory": dict_row, "autocommit": False},
        )
    return _PG_POOLS[database_url]


def mask_database_url(url: str) -> str:
    """Mask password credentials in database URL for safe logging/diagnostics."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username or ''}:***@{parsed.hostname or ''}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urllib.parse.urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        return "masked-database-url"


def is_postgres_target(db_target: Optional[Union[str, Path]] = None) -> bool:
    """Determine whether the specified or configured database target is PostgreSQL."""
    if db_target is not None:
        target_str = str(db_target).strip()
        if target_str.startswith("postgresql://") or target_str.startswith("postgres://"):
            return True
        return False
    
    url = config.get_database_url()
    return url.startswith("postgresql://") or url.startswith("postgres://")


def get_database_path(db_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve the authoritative SQLite database path.
    
    If an explicit db_path is provided (e.g. by tests), use it.
    Otherwise delegate to config.get_database_path() which checks
    DATABASE_PATH env var → /data mount → local fallback.
    """
    if db_path is not None and not is_postgres_target(db_path):
        return Path(db_path).resolve()
    return config.get_database_path()


class DBCursor:
    """Unified cursor adapter abstracting SQLite and PostgreSQL."""

    def __init__(self, raw_cursor: Any, is_postgres: bool):
        self._cursor = raw_cursor
        self._is_postgres = is_postgres

    def _translate_query(self, query: str) -> str:
        if not self._is_postgres:
            return query
        # Replace ? parameter placeholders with %s for psycopg
        # SQLite uses ? while PostgreSQL psycopg uses %s
        return query.replace("?", "%s")

    def execute(self, query: str, params: Optional[Union[Sequence[Any], Dict[str, Any]]] = None) -> "DBCursor":
        translated = self._translate_query(query)
        if params is not None:
            # If params is a single dict or sequence
            if self._is_postgres and isinstance(params, (list, tuple)):
                # Convert any json structures if necessary
                processed_params = []
                for p in params:
                    processed_params.append(p)
                self._cursor.execute(translated, tuple(processed_params))
            else:
                self._cursor.execute(translated, params)
        else:
            self._cursor.execute(translated)
        return self

    def executescript(self, script: str) -> "DBCursor":
        if not self._is_postgres:
            self._cursor.executescript(script)
            return self

        # PostgreSQL: split into individual statements and execute
        # Remove SQL comments and empty statements
        cleaned = re.sub(r"--.*$", "", script, flags=re.MULTILINE)
        statements = [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]
        for stmt in statements:
            self._cursor.execute(stmt)
        return self

    def fetchone(self) -> Optional[Dict[str, Any]]:
        row = self._cursor.fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        if hasattr(row, "keys"):
            # sqlite3.Row or similar dict-like mapping
            return {k: row[k] for k in row.keys()}
        if isinstance(row, (tuple, list)):
            return dict(enumerate(row))
        return row

    def fetchall(self) -> List[Dict[str, Any]]:
        rows = self._cursor.fetchall()
        if not rows:
            return []
        res = []
        for r in rows:
            if isinstance(r, dict):
                res.append(r)
            elif hasattr(r, "keys"):
                res.append({k: r[k] for k in r.keys()})
            else:
                res.append(r)
        return res

    @property
    def rowcount(self) -> int:
        return getattr(self._cursor, "rowcount", -1)

    def close(self):
        try:
            self._cursor.close()
        except Exception:
            pass


class DBConnection:
    """Unified database connection wrapper providing transactional execution for SQLite & PostgreSQL."""

    def __init__(self, raw_conn: Any, is_postgres: bool, pool_conn: bool = False, pool: Any = None):
        self._conn = raw_conn
        self._is_postgres = is_postgres
        self._pool_conn = pool_conn
        self._pool = pool
        self._closed = False

    @property
    def is_postgres(self) -> bool:
        return self._is_postgres

    def cursor(self) -> DBCursor:
        raw_cur = self._conn.cursor()
        return DBCursor(raw_cur, self._is_postgres)

    def commit(self):
        if self._conn and not self._closed:
            self._conn.commit()

    def rollback(self):
        if self._conn and not self._closed:
            try:
                self._conn.rollback()
            except Exception:
                pass

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self._pool and self._pool_conn:
            try:
                self._pool.putconn(self._conn)
            except Exception:
                pass
        else:
            try:
                self._conn.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db_connection(db_target: Optional[Union[str, Path]] = None) -> DBConnection:
    """Obtain an authoritative database connection for PostgreSQL or SQLite."""
    if is_postgres_target(db_target):
        url = str(db_target).strip() if db_target is not None else config.get_database_url()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]

        if not HAS_PSYCOPG:
            raise RuntimeError(
                "psycopg is required to connect to PostgreSQL. Run: pip install psycopg[binary] psycopg-pool"
            )

        try:
            # Use connection pool for high concurrency and reuse
            pool = get_pg_pool(url)
            raw_conn = pool.getconn()
            return DBConnection(raw_conn, is_postgres=True, pool_conn=True, pool=pool)
        except Exception as e:
            logger.warning("Connection pool failed (%s), falling back to direct psycopg.connect", e)
            raw_conn = psycopg.connect(url, row_factory=dict_row, autocommit=False)
            return DBConnection(raw_conn, is_postgres=True, pool_conn=False)

    # SQLite connection
    target_path = get_database_path(db_target)
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error("Failed to ensure SQLite database directory %s exists: %s", target_path.parent, e)

    sqlite_conn = sqlite3.connect(str(target_path), timeout=30.0)
    try:
        sqlite_conn.execute("PRAGMA foreign_keys = ON")
        sqlite_conn.execute("PRAGMA journal_mode = WAL")
        sqlite_conn.execute("PRAGMA busy_timeout = 5000")
    except Exception as e:
        logger.warning("Could not set SQLite PRAGMAs on %s: %s", target_path, e)
    sqlite_conn.row_factory = sqlite3.Row
    return DBConnection(sqlite_conn, is_postgres=False)


def hash_password(password: str, salt: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and per-user salt."""
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return key.hex()


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify a password against a stored hash using constant-time comparison."""
    if not password or not password_hash or not salt:
        return False
    computed_hash = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, password_hash)


def get_database_diagnostics(db_target: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Report safe runtime database diagnostic metrics without exposing secrets."""
    is_pg = is_postgres_target(db_target)
    
    if is_pg:
        raw_url = str(db_target).strip() if db_target is not None else config.get_database_url()
        masked_url = mask_database_url(raw_url)
        engine = "postgresql"
        resolved_target = masked_url
        is_persistent = True
        journal_mode = "native-wal"
        foreign_keys = True
        file_exists = True
        file_size = 0
        parent_dir = "n/a (managed cloud database)"
        parent_exists = True
        parent_writable = True
    else:
        target_path = get_database_path(db_target)
        file_exists = target_path.is_file()
        file_size = target_path.stat().st_size if file_exists else 0
        parent_dir = str(target_path.parent)
        parent_exists = target_path.parent.exists()
        parent_writable = os.access(str(target_path.parent), os.W_OK) if parent_exists else False
        is_persistent = str(target_path).startswith("/data") or str(parent_dir).startswith("/data")
        engine = "sqlite"
        resolved_target = str(target_path)
        journal_mode = "unknown"
        foreign_keys = False

    user_count = 0
    board_count = 0
    card_count = 0
    session_count = 0

    try:
        conn = get_db_connection(db_target)
        cursor = conn.cursor()

        if not is_pg:
            try:
                cursor.execute("PRAGMA journal_mode")
                row = cursor.fetchone()
                if row:
                    journal_mode = str(list(row.values())[0] if isinstance(row, dict) else row[0])
            except Exception as e:
                logger.warning("Could not read PRAGMA journal_mode: %s", e)

            try:
                cursor.execute("PRAGMA foreign_keys")
                row = cursor.fetchone()
                if row:
                    val = list(row.values())[0] if isinstance(row, dict) else row[0]
                    foreign_keys = bool(int(val))
            except Exception as e:
                logger.warning("Could not read PRAGMA foreign_keys: %s", e)

        try:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            row = cursor.fetchone()
            user_count = int(row["count"]) if row else 0
        except Exception as e:
            logger.warning("Could not count users: %s", e)

        try:
            cursor.execute("SELECT COUNT(*) as count FROM boards")
            row = cursor.fetchone()
            board_count = int(row["count"]) if row else 0
        except Exception as e:
            logger.warning("Could not count boards: %s", e)

        try:
            cursor.execute("SELECT COUNT(*) as count FROM cards")
            row = cursor.fetchone()
            card_count = int(row["count"]) if row else 0
        except Exception as e:
            logger.warning("Could not count cards: %s", e)

        try:
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            row = cursor.fetchone()
            session_count = int(row["count"]) if row else 0
        except Exception as e:
            logger.warning("Could not count sessions: %s", e)

        conn.close()
    except Exception as e:
        logger.error("Error collecting database diagnostics: %s", e)

    return {
        "engine": engine,
        "configuredUrl": mask_database_url(os.getenv("DATABASE_URL", "").strip()) or None,
        "configuredPath": os.getenv("DATABASE_PATH", "").strip() or None,
        "resolvedPath": resolved_target,
        "fileExists": file_exists,
        "fileSizeBytes": file_size,
        "parentDirectory": parent_dir,
        "parentExists": parent_exists,
        "parentWritable": parent_writable,
        "isPersistentMount": is_persistent,
        "journalMode": journal_mode,
        "foreignKeysEnabled": foreign_keys,
        "userCount": user_count,
        "boardCount": board_count,
        "cardCount": card_count,
        "sessionCount": session_count,
    }


def init_db(db_target: Optional[Union[str, Path]] = None):
    """Initialize database schema, indexes, and safe migrations ONLY.
    Works seamlessly and idempotently across PostgreSQL and SQLite.
    Never auto-seeds demo/default users or recreates deleted data on production startup.
    """
    conn = get_db_connection(db_target)
    cursor = conn.cursor()

    is_pg = conn.is_postgres

    # 1. Base DDL statements (Standard ANSI SQL valid in both SQLite and PostgreSQL)
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS boards (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS columns (
            id TEXT PRIMARY KEY,
            board_id TEXT NOT NULL,
            title TEXT NOT NULL,
            position INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
        )
        """,
        """
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
        )
        """,
        """
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
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS project_members (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES boards(id) ON DELETE CASCADE,
            UNIQUE(project_id, user_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            project_id TEXT DEFAULT NULL,
            type TEXT NOT NULL DEFAULT 'system',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        # Indexes
        "CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id)",
        "CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_log_project_id ON activity_log(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_log_project_created ON activity_log(project_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_project_members_user_project ON project_members(user_id, project_id)",
        "CREATE INDEX IF NOT EXISTS idx_cards_due_date ON cards(due_date)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)",
    ]

    for stmt in ddl_statements:
        cursor.execute(stmt.strip())

    # 2. Safe Column Migrations for existing schemas
    if is_pg:
        # PostgreSQL supports ADD COLUMN IF NOT EXISTS natively
        pg_migrations = [
            "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP",
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''",
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'medium'",
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS due_date TEXT DEFAULT NULL",
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS tags TEXT DEFAULT '[]'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_salt TEXT NOT NULL DEFAULT 'legacy'",
        ]
        for mig in pg_migrations:
            try:
                cursor.execute(mig)
            except Exception as e:
                logger.warning("PostgreSQL migration notice (%s): %s", mig, e)
    else:
        # SQLite schema inspection
        try:
            cursor.execute("PRAGMA table_info(sessions)")
            sess_cols = {row["name"] for row in cursor.fetchall()}
            if "expires_at" not in sess_cols:
                cursor.execute("ALTER TABLE sessions ADD COLUMN expires_at TIMESTAMP")

            cursor.execute("PRAGMA table_info(cards)")
            card_cols = {row["name"] for row in cursor.fetchall()}
            if "description" not in card_cols:
                cursor.execute("ALTER TABLE cards ADD COLUMN description TEXT DEFAULT ''")
            if "priority" not in card_cols:
                cursor.execute("ALTER TABLE cards ADD COLUMN priority TEXT DEFAULT 'medium'")
            if "due_date" not in card_cols:
                cursor.execute("ALTER TABLE cards ADD COLUMN due_date TEXT DEFAULT NULL")
            if "tags" not in card_cols:
                cursor.execute("ALTER TABLE cards ADD COLUMN tags TEXT DEFAULT '[]'")

            cursor.execute("PRAGMA table_info(users)")
            user_cols = {row["name"] for row in cursor.fetchall()}
            if "password_salt" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN password_salt TEXT NOT NULL DEFAULT 'legacy'")
        except Exception as e:
            logger.warning("SQLite migration check notice: %s", e)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully (engine=%s)", "postgresql" if is_pg else "sqlite")


def create_session(username: str, db_path: Optional[Union[str, Path]] = None, duration_days: int = 7) -> dict:
    """Create a new session for an existing user with an expiration timestamp."""
    username_clean = username.strip().lower()
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users WHERE LOWER(username) = ?", (username_clean,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Cannot create session: user '{username_clean}' does not exist.")

    user_id = row["id"]
    token = f"sess-{secrets.token_hex(24)}"
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=duration_days)).isoformat()

    cursor.execute(
        "INSERT INTO sessions (token, user_id, username, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
        (token, user_id, row["username"], now.isoformat(), expires_at),
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "user": row["username"],
        "userId": user_id,
        "token": token,
        "expiresAt": expires_at,
    }


def verify_session_token(token: str, db_path: Optional[Union[str, Path]] = None) -> Optional[dict]:
    """Verify a session token against the database, enforcing expiration."""
    if not token or not isinstance(token, str):
        return None
    clean_token = token.strip()
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT token, user_id, username, expires_at FROM sessions WHERE token = ?",
        (clean_token,)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Enforce session expiration
    expires_at = row["expires_at"]
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(str(expires_at))
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp_dt:
                cursor.execute("DELETE FROM sessions WHERE token = ?", (clean_token,))
                conn.commit()
                conn.close()
                return None
        except Exception:
            pass

    conn.close()
    return {"userId": row["user_id"], "username": row["username"]}


def revoke_session(token: str, db_path: Optional[Union[str, Path]] = None) -> bool:
    """Revoke/delete an active session."""
    if not token:
        return False
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token.strip(),))
    conn.commit()
    conn.close()
    return True


def register_user(username: str, password: str, db_path: Optional[Union[str, Path]] = None) -> dict:
    """Register a unique user account, hash the password with a cryptographic salt,
    verify persistence immediately, and initialize their first project.
    """
    username_clean = username.strip().lower()
    if not username_clean or len(password) < 4:
        return {"success": False, "error": "Username must be non-empty and password at least 4 characters."}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username_clean,))
        existing_row = cursor.fetchone()
        if existing_row:
            conn.close()
            return {"success": False, "error": "Username is already taken."}

        user_id = f"user-{uuid.uuid4().hex[:8]}"
        salt = secrets.token_hex(16)
        hashed = hash_password(password, salt)

        cursor.execute(
            "INSERT INTO users (id, username, password_hash, password_salt) VALUES (?, ?, ?, ?)",
            (user_id, username_clean, hashed, salt),
        )
        conn.commit()

        # Immediate verification query-back to ensure persistence
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        verified = cursor.fetchone()
        if not verified or verified["username"].lower() != username_clean:
            conn.rollback()
            conn.close()
            logger.error("REGISTER_FAILED verification query failed for user=%s", username_clean)
            return {"success": False, "error": "Failed to persist user credentials to database."}

        conn.close()
        logger.info("REGISTER user=%s committed=true", username_clean)

        # Create initial starter project once for the newly verified user
        create_project(username_clean, name="Main Project", db_path=db_path)

        # Generate authenticated session
        return create_session(username_clean, db_path=db_path)
    except Exception as e:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        logger.error("REGISTER_ERROR user=%s error=%s", username_clean, e)
        return {"success": False, "error": f"Registration failed: {str(e)}"}


def authenticate_user(username: str, password: str, db_path: Optional[Union[str, Path]] = None) -> Optional[dict]:
    """Authenticate a user using constant-time password hash verification against the authoritative database."""
    username_clean = username.strip().lower()
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, username, password_hash, password_salt FROM users WHERE LOWER(username) = ?",
            (username_clean,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            logger.warning("LOGIN_FAILED user=%s reason=user_not_found", username_clean)
            return None

        salt = row["password_salt"] or "legacy"
        if verify_password(password, row["password_hash"], salt):
            logger.info("LOGIN_SUCCESS user=%s", username_clean)
            return create_session(row["username"], db_path=db_path)

        # Legacy backward compatibility check with old static salt if migrating
        if salt == "legacy" and verify_password(password, row["password_hash"], "drag_n_drop_salt"):
            logger.info("LOGIN_SUCCESS_LEGACY user=%s", username_clean)
            return create_session(row["username"], db_path=db_path)

        logger.warning("LOGIN_FAILED user=%s reason=invalid_password", username_clean)
        return None
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        logger.error("LOGIN_ERROR user=%s error=%s", username_clean, e)
        return None


def get_projects(user_id: str, db_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Retrieve all projects accessible to the authenticated user.
    Never resurrects a deleted project if the list is empty.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    username_clean = user_id.strip().lower()
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username_clean,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return []

    internal_user_id = user_row["id"]
    cursor.execute(
        """
        SELECT DISTINCT b.id, b.name, b.created_at, b.updated_at
        FROM boards b
        LEFT JOIN project_members pm ON b.id = pm.project_id
        WHERE b.user_id = ? OR LOWER(pm.user_id) = ? OR pm.user_id = ?
        ORDER BY b.created_at ASC
        """,
        (internal_user_id, username_clean, internal_user_id),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "createdAt": str(row["created_at"]) if row.get("created_at") is not None else None,
            "updatedAt": str(row["updated_at"]) if row.get("updated_at") is not None else None,
        }
        for row in rows
    ]


def create_project(user_id: str, name: str = "New Project", db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Create a new project and its 5 initial columns in an atomic transaction."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    username_clean = user_id.strip().lower()
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username_clean,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        raise ValueError(f"Cannot create project: user '{username_clean}' does not exist.")

    internal_user_id = user_row["id"]
    project_id = f"board-{uuid.uuid4().hex[:8]}"

    cursor.execute(
        "INSERT INTO boards (id, user_id, name) VALUES (?, ?, ?)",
        (project_id, internal_user_id, name),
    )

    col_specs = [
        (f"col-backlog-{project_id[-6:]}", "Backlog", 0),
        (f"col-discovery-{project_id[-6:]}", "Discovery", 1),
        (f"col-progress-{project_id[-6:]}", "In Progress", 2),
        (f"col-review-{project_id[-6:]}", "Review", 3),
        (f"col-done-{project_id[-6:]}", "Done", 4),
    ]

    for col_id, col_title, col_pos in col_specs:
        cursor.execute(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            (col_id, project_id, col_title, col_pos),
        )

    # Register owner in project_members
    cursor.execute(
        "INSERT INTO project_members (id, project_id, user_id, role) VALUES (?, ?, ?, ?)",
        (f"pm-{uuid.uuid4().hex[:8]}", project_id, username_clean, "owner"),
    )

    conn.commit()
    log_activity(project_id, username_clean, "project_created", "project", project_id, f"Created project '{name}'", {"name": name}, db_path)

    cursor.execute("SELECT id, name, created_at, updated_at FROM boards WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    return {
        "id": row["id"],
        "name": row["name"],
        "createdAt": str(row["created_at"]) if row.get("created_at") is not None else None,
        "updatedAt": str(row["updated_at"]) if row.get("updated_at") is not None else None,
    }


def update_project(user_id: str, project_id: str, name: str, db_path: Optional[Union[str, Path]] = None) -> Optional[Dict[str, Any]]:
    """Rename a project, verifying user admin/owner permissions."""
    if not check_user_permission(project_id, user_id, "admin", db_path=db_path):
        return None

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE boards SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (name, project_id),
    )
    conn.commit()

    log_activity(project_id, user_id, "project_updated", "project", project_id, f"Renamed project to '{name}'", {"name": name}, db_path)

    cursor.execute("SELECT id, name, created_at, updated_at FROM boards WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "createdAt": str(row["created_at"]) if row.get("created_at") is not None else None,
        "updatedAt": str(row["updated_at"]) if row.get("updated_at") is not None else None,
    }


def delete_project(user_id: str, project_id: str, db_path: Optional[Union[str, Path]] = None) -> bool:
    """Delete a project and cascade delete all dependent data in an atomic transaction."""
    if not check_user_permission(project_id, user_id, "owner", db_path=db_path):
        return False

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM columns WHERE board_id = ?", (project_id,))
    cols = cursor.fetchall()
    for col in cols:
        cursor.execute("DELETE FROM cards WHERE column_id = ?", (col["id"],))
    cursor.execute("DELETE FROM columns WHERE board_id = ?", (project_id,))
    cursor.execute("DELETE FROM project_members WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM activity_log WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM boards WHERE id = ?", (project_id,))

    conn.commit()
    conn.close()
    return True


def get_board(user_id: str, db_path: Optional[Union[str, Path]] = None, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch authoritative board state (columns and cards) from the database."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    username_clean = user_id.strip().lower()
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username_clean,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return None

    internal_user_id = user_row["id"]
    target_project_id = project_id

    if not target_project_id:
        # Fall back to user's first accessible project
        cursor.execute(
            """
            SELECT b.id FROM boards b
            LEFT JOIN project_members pm ON b.id = pm.project_id
            WHERE b.user_id = ? OR LOWER(pm.user_id) = ? OR pm.user_id = ?
            ORDER BY b.created_at ASC LIMIT 1
            """,
            (internal_user_id, username_clean, internal_user_id),
        )
        row = cursor.fetchone()
        if row:
            target_project_id = row["id"]

    if not target_project_id:
        conn.close()
        return {"columns": [], "cards": {}}

    conn.close()
    if not check_user_permission(target_project_id, user_id, "viewer", db_path=db_path):
        return None

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position ASC",
        (target_project_id,),
    )
    col_rows = cursor.fetchall()

    columns = []
    cards_map = {}

    for col in col_rows:
        col_id = col["id"]
        cursor.execute(
            """
            SELECT id, title, details, description, priority, due_date, tags, assignee, position, created_at, updated_at
            FROM cards WHERE column_id = ? ORDER BY position ASC
            """,
            (col_id,),
        )
        card_rows = cursor.fetchall()
        card_ids = []
        for card in card_rows:
            card_id = card["id"]
            card_ids.append(card_id)
            tags_list = []
            if card.get("tags"):
                try:
                    tags_list = json.loads(card["tags"]) if isinstance(card["tags"], str) else card["tags"]
                except Exception:
                    tags_list = []

            det = card.get("details") or card.get("description") or ""
            desc = card.get("description") or card.get("details") or ""

            cards_map[card_id] = {
                "id": card_id,
                "title": card["title"],
                "details": det,
                "description": desc,
                "priority": card.get("priority") or "medium",
                "dueDate": card.get("due_date"),
                "tags": tags_list if isinstance(tags_list, list) else [],
                "assignee": card.get("assignee"),
                "createdAt": str(card["created_at"]) if card.get("created_at") is not None else None,
                "updatedAt": str(card["updated_at"]) if card.get("updated_at") is not None else None,
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
        "boardId": target_project_id,
        "userId": username_clean,
        "columns": columns,
        "cards": cards_map,
    }


def save_board(user_id: str, project_id: str, board_data: dict, db_path: Optional[Union[str, Path]] = None) -> Optional[Dict[str, Any]]:
    """Atomically and transactionally replace/update the full board state for a project."""
    if not check_user_permission(project_id, user_id, "member", db_path=db_path):
        return {"error": "Forbidden: insufficient permissions to update board"}

    raw_columns = board_data.get("columns", [])
    raw_cards = board_data.get("cards", {})

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        # 1. Fetch existing columns for this project
        cursor.execute("SELECT id FROM columns WHERE board_id = ?", (project_id,))
        existing_col_ids = {row["id"] for row in cursor.fetchall()}
        submitted_col_ids = set()

        # 2. Sync columns
        for col_pos, col_item in enumerate(raw_columns):
            col_id = col_item.get("id") or f"col-{uuid.uuid4().hex[:8]}"
            col_title = col_item.get("title") or f"Column {col_pos + 1}"
            submitted_col_ids.add(col_id)

            if col_id in existing_col_ids:
                cursor.execute(
                    "UPDATE columns SET title = ?, position = ? WHERE id = ? AND board_id = ?",
                    (col_title, col_pos, col_id, project_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
                    (col_id, project_id, col_title, col_pos),
                )

        # Delete columns no longer present in submitted board
        cols_to_delete = existing_col_ids - submitted_col_ids
        for del_col_id in cols_to_delete:
            cursor.execute("DELETE FROM cards WHERE column_id = ?", (del_col_id,))
            cursor.execute("DELETE FROM columns WHERE id = ?", (del_col_id,))

        # 3. Fetch existing cards across all remaining columns of this project
        cursor.execute(
            "SELECT c.id FROM cards c JOIN columns col ON c.column_id = col.id WHERE col.board_id = ?",
            (project_id,),
        )
        existing_card_ids = {row["id"] for row in cursor.fetchall()}
        submitted_card_ids = set()

        # 4. Sync cards according to column cardIds order
        for col_item in raw_columns:
            col_id = col_item.get("id")
            card_ids = col_item.get("cardIds", [])
            for card_pos, cid in enumerate(card_ids):
                card_obj = raw_cards.get(cid)
                if not card_obj or not isinstance(card_obj, dict):
                    continue

                card_title = card_obj.get("title") or "Untitled Task"
                det = card_obj.get("details") or card_obj.get("description") or ""
                desc = card_obj.get("description") or card_obj.get("details") or ""
                priority = card_obj.get("priority") or "medium"
                due_date = card_obj.get("dueDate") or card_obj.get("due_date")
                tags_list = card_obj.get("tags") or []
                tags_json = json.dumps(tags_list) if isinstance(tags_list, list) else "[]"
                assignee = card_obj.get("assignee")
                submitted_card_ids.add(cid)

                if cid in existing_card_ids:
                    cursor.execute(
                        """
                        UPDATE cards
                        SET column_id = ?, title = ?, details = ?, description = ?, priority = ?, due_date = ?, tags = ?, assignee = ?, position = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (col_id, card_title, det, desc, priority, due_date, tags_json, assignee, card_pos, cid),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO cards (id, column_id, title, details, description, priority, due_date, tags, assignee, position)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (cid, col_id, card_title, det, desc, priority, due_date, tags_json, assignee, card_pos),
                    )

        # Also check any cards in raw_cards not in column cardIds but specifying columnId
        for cid, card_obj in raw_cards.items():
            if cid not in submitted_card_ids and isinstance(card_obj, dict):
                target_col_id = card_obj.get("columnId") or card_obj.get("column_id")
                if target_col_id and target_col_id in submitted_col_ids:
                    card_title = card_obj.get("title") or "Untitled Task"
                    det = card_obj.get("details") or card_obj.get("description") or ""
                    desc = card_obj.get("description") or card_obj.get("details") or ""
                    priority = card_obj.get("priority") or "medium"
                    due_date = card_obj.get("dueDate") or card_obj.get("due_date")
                    tags_list = card_obj.get("tags") or []
                    tags_json = json.dumps(tags_list) if isinstance(tags_list, list) else "[]"
                    assignee = card_obj.get("assignee")
                    submitted_card_ids.add(cid)

                    if cid in existing_card_ids:
                        cursor.execute(
                            """
                            UPDATE cards
                            SET column_id = ?, title = ?, details = ?, description = ?, priority = ?, due_date = ?, tags = ?, assignee = ?, position = 999, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                            """,
                            (target_col_id, card_title, det, desc, priority, due_date, tags_json, assignee, cid),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO cards (id, column_id, title, details, description, priority, due_date, tags, assignee, position)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 999)
                            """,
                            (cid, target_col_id, card_title, det, desc, priority, due_date, tags_json, assignee),
                        )

        # 5. Delete cards that belong to this project but were omitted from submitted board
        cards_to_delete = existing_card_ids - submitted_card_ids
        for del_card_id in cards_to_delete:
            cursor.execute("DELETE FROM cards WHERE id = ?", (del_card_id,))

        # 6. Update project timestamp
        cursor.execute("UPDATE boards SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))

        conn.commit()
        conn.close()

        log_activity(project_id, user_id, "board_saved", "board", project_id, "Saved full board layout", {}, db_path=db_path)
        return get_board(user_id, db_path, project_id=project_id)
    except Exception as e:
        logger.error("Failed to save full board transactionally for project %s: %s", project_id, e)
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        raise


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
    db_path: Optional[Union[str, Path]] = None,
):
    """Add a card to a column, verifying member permissions on the project."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT board_id FROM columns WHERE id = ?", (column_id,))
    col_row = cursor.fetchone()
    if not col_row:
        conn.close()
        return None

    project_id = col_row["board_id"]
    conn.close()

    if not check_user_permission(project_id, user_id, "member", db_path=db_path):
        return {"error": "Forbidden: insufficient permissions to add card"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM cards WHERE column_id = ?", (column_id,))
    count_row = cursor.fetchone()
    count = count_row["count"] if count_row else 0

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
        "createdAt": str(row["created_at"]) if row and row.get("created_at") is not None else None,
        "updatedAt": str(row["updated_at"]) if row and row.get("updated_at") is not None else None,
    }


def update_card(card_id: str, updates: dict, user_id: str, db_path: Optional[Union[str, Path]] = None):
    """Update card attributes atomically, verifying tenant permissions."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT c.*, col.board_id FROM cards c JOIN columns col ON c.column_id = col.id WHERE c.id = ?", (card_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return None

    project_id = existing["board_id"]
    conn.close()

    if not check_user_permission(project_id, user_id, "member", db_path=db_path):
        return {"error": "Forbidden: insufficient permissions to update card"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

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
    if updated_row.get("tags"):
        try:
            tags_list = json.loads(updated_row["tags"]) if isinstance(updated_row["tags"], str) else updated_row["tags"]
        except Exception:
            tags_list = []

    card_title = updated_row["title"]
    log_activity(project_id, user_id, "card_updated", "card", card_id, f"Updated task '{card_title}'", updates, db_path=db_path)

    return {
        "id": updated_row["id"],
        "title": updated_row["title"],
        "details": updated_row.get("details") or updated_row.get("description") or "",
        "description": updated_row.get("description") or updated_row.get("details") or "",
        "priority": updated_row.get("priority") or "medium",
        "dueDate": updated_row.get("due_date"),
        "tags": tags_list if isinstance(tags_list, list) else [],
        "assignee": updated_row.get("assignee"),
        "createdAt": str(updated_row["created_at"]) if updated_row.get("created_at") is not None else None,
        "updatedAt": str(updated_row["updated_at"]) if updated_row.get("updated_at") is not None else None,
    }


def delete_card(card_id: str, user_id: str, db_path: Optional[Union[str, Path]] = None):
    """Permanently delete a card from the database and verify deletion."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT c.title, col.board_id FROM cards c JOIN columns col ON c.column_id = col.id WHERE c.id = ?", (card_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return False

    project_id = existing["board_id"]
    conn.close()

    if not check_user_permission(project_id, user_id, "member", db_path=db_path):
        return {"error": "Forbidden: insufficient permissions to delete card"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    card_title = existing["title"]

    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()

    # Post-deletion verification
    cursor.execute("SELECT id FROM cards WHERE id = ?", (card_id,))
    check_row = cursor.fetchone()
    conn.close()

    if check_row is not None:
        raise RuntimeError(f"Database deletion failed for card {card_id}")

    log_activity(project_id, user_id, "card_deleted", "card", card_id, f"Deleted task '{card_title}'", {"title": card_title}, db_path=db_path)
    return True


def move_card(card_id: str, destination_column_id: str, position: int = 0, user_id: str = "user", db_path: Optional[Union[str, Path]] = None):
    """Move a card to a destination column at a specific position atomically."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT c.title, c.column_id, col.board_id FROM cards c JOIN columns col ON c.column_id = col.id WHERE c.id = ?", (card_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return None

    project_id = existing["board_id"]
    conn.close()

    if not check_user_permission(project_id, user_id, "member", db_path=db_path):
        return {"error": "Forbidden: insufficient permissions to move card"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Verify destination column belongs to same project
    cursor.execute("SELECT id FROM columns WHERE id = ? AND board_id = ?", (destination_column_id, project_id))
    dest_col = cursor.fetchone()
    if not dest_col:
        conn.close()
        return None

    cursor.execute(
        "UPDATE cards SET column_id = ?, position = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (destination_column_id, position, card_id),
    )
    conn.commit()
    conn.close()

    log_activity(
        project_id,
        user_id,
        "card_moved",
        "card",
        card_id,
        f"Moved task '{existing['title']}'",
        {"destinationColumnId": destination_column_id, "position": position},
        db_path=db_path,
    )

    return get_board(user_id, db_path, project_id=project_id)


def update_column(column_id: str, title: str, user_id: str, db_path: Optional[Union[str, Path]] = None):
    """Rename a column in a project."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT board_id FROM columns WHERE id = ?", (column_id,))
    col_row = cursor.fetchone()
    if not col_row:
        conn.close()
        return None

    project_id = col_row["board_id"]
    conn.close()

    if not check_user_permission(project_id, user_id, "member", db_path=db_path):
        return {"error": "Forbidden: insufficient permissions to update column"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE columns SET title = ? WHERE id = ?", (title, column_id))
    conn.commit()
    conn.close()

    log_activity(project_id, user_id, "column_updated", "column", column_id, f"Renamed column to '{title}'", {"title": title}, db_path=db_path)
    return {"id": column_id, "title": title}


def clear_column_cards(column_id: str, user_id: str, db_path: Optional[Union[str, Path]] = None):
    """Delete all cards within a column permanently."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT board_id, title FROM columns WHERE id = ?", (column_id,))
    col_row = cursor.fetchone()
    if not col_row:
        conn.close()
        return False

    project_id = col_row["board_id"]
    conn.close()

    if not check_user_permission(project_id, user_id, "member", db_path=db_path):
        return {"error": "Forbidden: insufficient permissions to clear column"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE column_id = ?", (column_id,))
    conn.commit()
    conn.close()

    log_activity(project_id, user_id, "column_cleared", "column", column_id, f"Cleared all cards from column '{col_row['title']}'", {}, db_path=db_path)
    return True


ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "member": 2,
    "viewer": 1,
    "none": 0,
}


def get_user_role(project_id: str, username: str, db_path: Optional[Union[str, Path]] = None) -> str:
    """Determine the user's role on a specific project strictly from the database."""
    if not project_id or not username:
        return "none"

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    username_clean = username.strip().lower()
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username_clean,))
    u_row = cursor.fetchone()
    if not u_row:
        conn.close()
        return "none"

    user_id = u_row["id"]

    # Check if direct project owner in boards table
    cursor.execute("SELECT user_id FROM boards WHERE id = ?", (project_id,))
    b_row = cursor.fetchone()
    if b_row and (b_row["user_id"] == user_id or b_row["user_id"] == username_clean):
        conn.close()
        return "owner"

    # Check project_members table
    cursor.execute(
        "SELECT role FROM project_members WHERE project_id = ? AND (LOWER(user_id) = ? OR user_id = ?)",
        (project_id, username_clean, user_id),
    )
    m_row = cursor.fetchone()
    conn.close()

    if m_row:
        return m_row["role"]

    return "none"


def check_user_permission(project_id: str, username: str, required_role: str = "viewer", db_path: Optional[Union[str, Path]] = None) -> bool:
    """Verify if the user meets the minimum required role for a project."""
    user_role = get_user_role(project_id, username, db_path=db_path)
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    req_level = ROLE_HIERARCHY.get(required_role, 1)
    return user_level >= req_level


def get_project_members(project_id: str, db_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """List all registered members and the owner for a project."""
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
        JOIN users u ON pm.user_id = u.id OR LOWER(pm.user_id) = LOWER(u.username)
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
            "createdAt": str(owner_row["created_at"]) if owner_row.get("created_at") is not None else None,
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
                "createdAt": str(r["created_at"]) if r.get("created_at") is not None else None,
            })

    return members


def add_project_member(project_id: str, target_username: str, role: str, requesting_username: str, db_path: Optional[Union[str, Path]] = None):
    """Add an existing user to a project with a specific role."""
    if not check_user_permission(project_id, requesting_username, "admin", db_path=db_path):
        return {"success": False, "error": "Insufficient permissions to add project members."}

    target_clean = target_username.strip().lower()
    if role not in ROLE_HIERARCHY or role == "none":
        role = "member"

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users WHERE LOWER(username) = ?", (target_clean,))
    t_user = cursor.fetchone()
    if not t_user:
        conn.close()
        return {"success": False, "error": f"User '{target_clean}' does not exist."}

    target_user_id = t_user["id"]
    member_id = f"pm-{uuid.uuid4().hex[:8]}"

    # Check if member already exists
    cursor.execute(
        "SELECT id FROM project_members WHERE project_id = ? AND (user_id = ? OR LOWER(user_id) = ?)",
        (project_id, target_user_id, target_clean),
    )
    existing_m = cursor.fetchone()
    if existing_m:
        cursor.execute(
            "UPDATE project_members SET role = ? WHERE id = ?",
            (role, existing_m["id"]),
        )
    else:
        cursor.execute(
            "INSERT INTO project_members (id, project_id, user_id, role) VALUES (?, ?, ?, ?)",
            (member_id, project_id, target_user_id, role),
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


def remove_project_member(project_id: str, target_username: str, requesting_username: str, db_path: Optional[Union[str, Path]] = None):
    """Remove a user from project members."""
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
    if b_row and (b_row["user_id"] == t_user["id"] or b_row["user_id"] == target_clean):
        conn.close()
        return {"success": False, "error": "Cannot remove project owner."}

    cursor.execute(
        "DELETE FROM project_members WHERE project_id = ? AND (user_id = ? OR LOWER(user_id) = ?)",
        (project_id, t_user["id"], target_clean),
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


def log_activity(
    project_id: str,
    user_id: str,
    action_type: str,
    entity_type: str,
    entity_id: str,
    message: str,
    details: dict = None,
    db_path: Optional[Union[str, Path]] = None,
):
    """Log an audit event for a project."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    log_id = f"act-{uuid.uuid4().hex[:8]}"
    details_str = json.dumps(details or {})
    cursor.execute(
        """
        INSERT INTO activity_log (id, project_id, user_id, action_type, entity_type, entity_id, message, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (log_id, project_id, user_id, action_type, entity_type, entity_id, message, details_str),
    )
    conn.commit()
    conn.close()
    return log_id


def get_project_activities(project_id: str, user_id: str, limit: int = 50, offset: int = 0, db_path: Optional[Union[str, Path]] = None):
    """Retrieve audit history for a project with pagination."""
    if not check_user_permission(project_id, user_id, "viewer", db_path=db_path):
        return []

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Portable ordering: created_at DESC, id DESC
    cursor.execute(
        """
        SELECT id, project_id, user_id, action_type, entity_type, entity_id, message, details, created_at
        FROM activity_log
        WHERE project_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        (project_id, limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()

    res = []
    for r in rows:
        dt = {}
        if r.get("details"):
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
            "createdAt": str(r["created_at"]) if r.get("created_at") is not None else None,
        })
    return res


def create_notification(
    user_id: str,
    project_id: Optional[str],
    notif_type: str,
    title: str,
    message: str,
    db_path: Optional[Union[str, Path]] = None,
):
    """Create a user notification."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    notif_id = f"notif-{uuid.uuid4().hex[:8]}"

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


def check_and_generate_due_date_notifications(username: str, db_path: Optional[Union[str, Path]] = None):
    """Generate notifications for upcoming task due dates."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    u_row = cursor.fetchone()
    if not u_row:
        conn.close()
        return

    user_id = u_row["id"]

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


def get_user_notifications(username: str, limit: int = 50, offset: int = 0, db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Retrieve paginated notifications for the authenticated user."""
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
            "projectId": r.get("project_id"),
            "type": r["type"],
            "title": r["title"],
            "message": r["message"],
            "isRead": is_read_bool,
            "createdAt": str(r["created_at"]) if r.get("created_at") is not None else None,
        })

    return {"notifications": notifications, "unreadCount": unread_count}


def mark_notification_as_read(notif_id: str, username: str, db_path: Optional[Union[str, Path]] = None):
    """Mark an unread notification as read."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND LOWER(user_id) = LOWER(?)",
        (notif_id, username),
    )
    conn.commit()
    conn.close()
    return True


def mark_all_notifications_read(username: str, db_path: Optional[Union[str, Path]] = None):
    """Mark all notifications as read for the user."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE LOWER(user_id) = LOWER(?)",
        (username,),
    )
    conn.commit()
    conn.close()
    return True
