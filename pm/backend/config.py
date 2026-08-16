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
def get_database_path() -> Path:
    """Authoritative database path resolver.
    
    Order of precedence:
    1. DATABASE_PATH environment variable (if explicitly set)
    2. Render Persistent Disk mount directory (/data/pm.db if /data is a directory)
    3. Container data directory (BASE_DIR / data / pm.db if exists)
    4. Local development file BASE_DIR / pm.db
    """
    env_path = os.getenv("DATABASE_PATH", "").strip()
    if env_path:
        return Path(env_path).resolve()

    render_data_dir = Path("/data")
    if render_data_dir.exists() and render_data_dir.is_dir():
        return (render_data_dir / "pm.db").resolve()

    container_data_dir = BASE_DIR / "data"
    if container_data_dir.exists() and container_data_dir.is_dir():
        return (container_data_dir / "pm.db").resolve()

    return (BASE_DIR / "pm.db").resolve()


DATABASE_PATH = os.getenv("DATABASE_PATH", "").strip()



