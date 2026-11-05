"""테스트 공통 준비물. 실제 DB와 Gemini 없이 돌도록 가짜 객체로 바꿔 끼운다."""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

import webapp.app as app_module
from src.domain import Chunk, SearchResult
from webapp import rate_limit
from webapp.dependency import chat_manager_dependency, retriever_manager_dependency
from webapp.routers import chat as chat_router

SOURCES = [
    SearchResult(Chunk(0, "01_about.md", "소개 > 경력", "클라우드 엔지니어로 일했습니다."), 0.84),
    SearchResult(Chunk(1, "03_projects.md", "프로젝트 > RAG 챗봇", "자기소개 RAG 챗봇을 만들었습니다."), 0.71),
]


class FakePool:
    """asyncpg 풀 대신 실행한 SQL과 값을 기록만 한다."""

    def __init__(self):
        self.executed: list[tuple[str, tuple]] = []

    async def execute(self, sql: str, *args) -> None:
        self.executed.append((sql, args))

    async def close(self) -> None:
        pass

    @property
    def chat_logs(self) -> list[dict]:
        # ChatLogRepository.insert 의 값 순서
        keys = ("visitor", "question", "history_turns", "status", "error",
                "answer", "answer_chars", "first_token_ms", "duration_ms", "sources")
        return [dict(zip(keys, args)) for sql, args in self.executed if sql.startswith("INSERT INTO chat_log")]


class FakeRetriever:
    def __init__(self, results: list[SearchResult]):
        self.results = results
        self.calls: list[tuple[str, str]] = []

    async def search(self, question: str, prev_question: str = "") -> list[SearchResult]:
        self.calls.append((question, prev_question))
        return self.results


class FakeChat:
    """정해 둔 조각을 차례로 내보내고, error 가 있으면 마지막에 그 오류를 낸다."""

    def __init__(self, pieces: list[str] = (), error: Exception | None = None):
        self.pieces = list(pieces)
        self.error = error

    async def stream_answer(self, question, history, results):
        for piece in self.pieces:
            yield piece
        if self.error:
            raise self.error


@pytest.fixture(autouse=True)
def reset_rate_limit():
    # IP별 요청 기록은 모듈 전역이라 테스트끼리 섞이지 않게 비운다
    rate_limit._hits.clear()


@pytest.fixture
def pool(monkeypatch) -> FakePool:
    pool = FakePool()

    async def fake_create_pool(url: str) -> FakePool:
        return pool

    monkeypatch.setattr(app_module, "create_pool", fake_create_pool)
    return pool


@pytest.fixture
def retriever() -> FakeRetriever:
    return FakeRetriever(SOURCES)


@pytest.fixture
def app(pool, retriever):
    app = app_module.create_app()
    app.dependency_overrides[retriever_manager_dependency] = lambda: retriever
    app.dependency_overrides[chat_manager_dependency] = lambda: FakeChat(["안녕", "하세요"])
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


def use_chat(app, chat) -> None:
    app.dependency_overrides[chat_manager_dependency] = lambda: chat


def wait_for_logs(client: TestClient) -> None:
    """질문 기록은 응답과 따로 저장되므로, 남은 저장 태스크가 끝날 때까지 기다린다."""

    async def drain() -> None:
        await asyncio.gather(*chat_router._background)

    client.portal.call(drain)


def sse_events(body: str) -> list[tuple[str, object]]:
    events = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((fields["event"], json.loads(fields["data"])))
    return events
