import os
from pathlib import Path

from dotenv import load_dotenv

SYSTEM_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = SYSTEM_DIR.parent
load_dotenv(SYSTEM_DIR / ".env")


class Settings:
    owner_name: str = os.getenv("OWNER_NAME", "한승재")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None
    # "-latest" 별칭은 Google이 최신 Flash 모델로 자동 연결해준다 (특정 버전 고정 시 모델 ID로 변경)
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    voyage_api_key: str | None = os.getenv("VOYAGE_API_KEY") or None
    # 출력 차원(1024)이 deploy/local/postgresql/00-init.sql 의 vector(1024)와 같아야 한다
    voyage_model: str = os.getenv("VOYAGE_MODEL", "voyage-3.5")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://rag:rag@localhost:5433/rag_portfolio")

    profile_dir: Path = SYSTEM_DIR / "dataset" / "profile"
    web_dir: Path = PROJECTS_DIR / "web"

    top_k: int = 4
    rate_limit: int = 20         # IP당 rate_window초 동안 허용하는 질문 수
    rate_window: int = 600


settings = Settings()
