from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.database.connection import create_pool
from src.settings import settings
from webapp.routers import chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await create_pool(settings.database_url)
    yield
    await app.state.db_pool.close()


def create_app() -> FastAPI:
    app = FastAPI(title=f"{settings.owner_name} 자기소개 RAG 챗봇", lifespan=lifespan)
    app.include_router(chat.router)

    # 프론트엔드(projects/web)를 같은 서버에서 제공한다
    app.mount("/static", StaticFiles(directory=settings.web_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def home():
        return FileResponse(settings.web_dir / "index.html")

    return app
