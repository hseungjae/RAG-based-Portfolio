import os
from pathlib import Path

from dotenv import load_dotenv

SYSTEM_DIR = Path(__file__).resolve().parent.parent
load_dotenv(SYSTEM_DIR / ".env")


class Settings:
    owner_name: str = os.getenv("OWNER_NAME", "한승재")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None
    # 무료 플랜 신규 키로 호출 가능한 모델 (2026-10 확인). 오래된 모델은 신규 사용자에게 404를 준다
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2-preview")
    # deploy/local/postgresql/00-init.sql 의 vector(1024)와 같아야 한다
    embedding_dimension: int = 1024
    database_url: str = os.getenv("DATABASE_URL", "postgresql://hseungjae:skills53%23@localhost:5433/sjhan")

    profile_dir: Path = SYSTEM_DIR / "dataset" / "profile"

    top_k: int = 4
    rate_limit: int = 20         # IP당 rate_window초 동안 허용하는 질문 수
    rate_window: int = 600


settings = Settings()
