import os
from pathlib import Path

from dotenv import load_dotenv

SYSTEM_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = SYSTEM_DIR.parent
load_dotenv(SYSTEM_DIR / ".env")


class Settings:
    owner_name: str = os.getenv("OWNER_NAME", "한승재")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")

    profile_dir: Path = SYSTEM_DIR / "dataset" / "profile"
    web_dir: Path = PROJECTS_DIR / "web"

    top_k: int = 4
    rate_limit: int = 20         # IP당 rate_window초 동안 허용하는 질문 수
    rate_window: int = 600


settings = Settings()
