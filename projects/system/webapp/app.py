import hashlib
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.database.connection import create_pool
from src.settings import settings
from webapp.routers import chat


def _versioned(match: re.Match) -> str:
    name = match.group(1)
    path = settings.web_dir / name
    if not path.is_file():
        return match.group(0)
    digest = hashlib.md5(path.read_bytes()).hexdigest()[:8]
    return f'"/static/{name}?v={digest}"'


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
        # CSS/JS 주소 뒤에 파일 내용 해시를 붙인다 (/static/app.js -> /static/app.js?v=3f2a9c1b).
        # Cloudflare가 정적 파일의 캐시 헤더를 4시간으로 덮어써도, 파일이 바뀌면 주소가 바뀌어 새로 받게 된다.
        html = (settings.web_dir / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(re.sub(r'"/static/([\w.-]+)"', _versioned, html))

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        # <link rel="icon">를 읽지 않는 브라우저·봇도 같은 아이콘을 받게 한다
        return FileResponse(settings.web_dir / "favicon.svg", media_type="image/svg+xml")

    @app.middleware("http")
    async def no_cache_frontend(request, call_next):
        # 브라우저가 예전 CSS/JS를 캐시해 새 HTML과 섞이지 않도록, 매번 서버에 변경 여부를 확인하게 한다.
        # 파일이 그대로면 ETag 덕분에 304 응답만 오가므로 부담은 거의 없다.
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    return app
