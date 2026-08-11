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
        load_dotenv(env_path)
        break
else:
    load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Production Hardening & Security Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "drag_n_drop_dev_secret_key_2026").strip()
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]
RATE_LIMIT_LOGIN_MAX = int(os.getenv("RATE_LIMIT_LOGIN_MAX", "15"))
RATE_LIMIT_LOGIN_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "60"))
