import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.chat_log.repository import ChatLogRepository
from src.database.connection import create_pool
from src.settings import settings
from webapp.metrics import http_metrics_middleware, metrics_endpoint
from webapp.routers import chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await create_pool(settings.database_url)
    await ChatLogRepository(app.state.db_pool).ensure_schema()
    yield
    await app.state.db_pool.close()


def create_app() -> FastAPI:
    # 앱 로그(rag.*)를 uvicorn 로그와 같은 모양으로 stdout 에 남긴다 (kubectl logs 로 확인).
    # 라이브러리(httpx 등)의 요청 로그는 경고 이상만 보이게 한다.
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s:     %(message)s")
    logging.getLogger("rag").setLevel(logging.INFO)

    # 화면은 projects/react-app(nginx)이 제공하고, 이 서버는 /api 와 /metrics 만 담당한다
    app = FastAPI(title=f"{settings.owner_name} 자기소개 RAG 챗봇", lifespan=lifespan)
    app.include_router(chat.router)
    app.middleware("http")(http_metrics_middleware)
    app.add_api_route("/metrics", metrics_endpoint, include_in_schema=False)
    return app
