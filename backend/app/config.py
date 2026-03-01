from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_ROOT / ".env"

# Always load backend/.env and override inherited shell variables to avoid
# accidentally using stale placeholder API keys from the host environment.
load_dotenv(dotenv_path=ENV_FILE, override=True)


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str
    openai_api_key: str
    openai_model: str
    openai_timeout_seconds: int
    sqlite_path: str
    cors_origins: list[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if "your_openai_api_key_here" in api_key.lower():
        api_key = ""

    cors = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        app_name="SafePlate API",
        openai_api_key=api_key,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o").strip(),
        openai_timeout_seconds=int(os.getenv("OPENAI_TIMEOUT_SECONDS", "90")),
        sqlite_path=os.getenv("SQLITE_PATH", "safeplate.db").strip(),
        cors_origins=_parse_csv(cors),
    )
