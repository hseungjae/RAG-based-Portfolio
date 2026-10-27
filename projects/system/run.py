"""FastAPI 서버 진입점.

    python run.py                # 0.0.0.0:8000
    python run.py --port 8001    # 포트 지정
    python run.py --reload       # 코드 저장 시 자동 재시작 (개발용)
"""

import argparse
import os

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="자기소개 RAG 챗봇 서버")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run("webapp.app:create_app", factory=True,
                host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
