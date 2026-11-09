import asyncio
from types import SimpleNamespace

import pytest
from google.genai import errors

from src.embedding.client import QUERY_PREFIX, EmbeddingClient


class FakeModels:
    """Gemini embed_content 대신 받은 모델·텍스트·설정을 기록한다."""

    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls = []

    async def embed_content(self, model, contents, config):
        if self.error:
            raise self.error
        self.calls.append((model, [c.parts[0].text for c in contents], config))
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.0]) for _ in contents])


def embedder_with(models: FakeModels) -> EmbeddingClient:
    embedder = EmbeddingClient(None, "gemini-embedding-2", 1024)
    embedder.client = SimpleNamespace(aio=SimpleNamespace(models=models))
    return embedder


def test_query_gets_search_prefix_without_task_type():
    models = FakeModels()

    asyncio.run(embedder_with(models).embed(["경력은?"], "query"))

    model, texts, config = models.calls[0]
    assert model == "gemini-embedding-2"
    assert texts == [QUERY_PREFIX + "경력은?"]
    # gemini-embedding-2는 task_type을 보내면 요청을 거절한다
    assert config.task_type is None
    assert config.output_dimensionality == 1024


def test_document_is_sent_as_given():
    models = FakeModels()

    asyncio.run(embedder_with(models).embed(["title: 소개 > 경력 | text: 클라우드"], "document"))

    assert models.calls[0][1] == ["title: 소개 > 경력 | text: 클라우드"]


def test_api_error_keeps_status_code():
    models = FakeModels(errors.ClientError(400, {"error": {"message": "bad request"}}))

    with pytest.raises(RuntimeError, match=r"\(400\)"):
        asyncio.run(embedder_with(models).embed(["경력은?"], "query"))
