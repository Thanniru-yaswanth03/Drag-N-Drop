import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Check multiple potential .env file locations
env_candidates = [
    BASE_DIR / ".env",
    BASE_DIR.parent / ".env",
    BASE_DIR.parent.parent / ".env",
]

for env_path in env_candidates:
    if env_path.exists():
        load_dotenv(env_path, override=True)
load_dotenv(override=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Production Hardening & Security Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()

_raw_secret_key = os.getenv("SECRET_KEY", "").strip()
if _raw_secret_key and _raw_secret_key != "drag_n_drop_dev_secret_key_2026":
    SECRET_KEY = _raw_secret_key
elif ENVIRONMENT in ("development", "test", ""):
    SECRET_KEY = _raw_secret_key or "drag_n_drop_dev_secret_key_2026"
else:
    raise RuntimeError(
        "CRITICAL CONFIGURATION ERROR: A dedicated SECRET_KEY environment variable is required in production. "
        "Set SECRET_KEY in your deployment environment or host dashboard."
    )

CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]
RATE_LIMIT_LOGIN_MAX = int(os.getenv("RATE_LIMIT_LOGIN_MAX", "15"))
RATE_LIMIT_LOGIN_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "60"))

# Database & Persistence Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def get_database_url() -> str:
    """Authoritative database connection URL resolver.
    
    Order of precedence:
    1. DATABASE_URL environment variable (PostgreSQL, SQLite URI, etc.)
    2. DATABASE_PATH environment variable (SQLite file path)
    3. Render Persistent Disk mount directory (/data/pm.db if /data is a directory)
    4. Local development file BASE_DIR / pm.db
    """
    raw_url = os.getenv("DATABASE_URL", "").strip()
    if raw_url:
        # Standardize postgres:// to postgresql:// for compatibility with psycopg/SQLAlchemy
        if raw_url.startswith("postgres://"):
            return "postgresql://" + raw_url[len("postgres://"):]
        return raw_url

    env_path = os.getenv("DATABASE_PATH", "").strip()
    if env_path:
        return f"sqlite:///{Path(env_path).resolve()}"

    render_data_dir = Path("/data")
    if render_data_dir.exists() and render_data_dir.is_dir():
        return f"sqlite:///{ (render_data_dir / 'pm.db').resolve() }"

    container_data_dir = BASE_DIR / "data"
    if container_data_dir.exists() and container_data_dir.is_dir():
        return f"sqlite:///{ (container_data_dir / 'pm.db').resolve() }"

    return f"sqlite:///{ (BASE_DIR / 'pm.db').resolve() }"


def get_database_path() -> Path:
    """Authoritative SQLite database path resolver for backwards compatibility."""
    url = get_database_url()
    if url.startswith("sqlite:///"):
        return Path(url[len("sqlite:///"):]).resolve()
    elif url.startswith("sqlite://"):
        return Path(url[len("sqlite://"):]).resolve()
    
    env_path = os.getenv("DATABASE_PATH", "").strip()
    if env_path:
        return Path(env_path).resolve()

    return (BASE_DIR / "pm.db").resolve()

