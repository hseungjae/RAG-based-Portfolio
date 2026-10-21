from functools import lru_cache

from fastapi import Request

from src.chat.manager import ChatManager
from src.chunk.repository import ChunkRepository
from src.embedding.client import EmbeddingClient
from src.retriever.manager import RetrieverManager
from src.settings import settings


@lru_cache
def embedding_client_dependency() -> EmbeddingClient:
    return EmbeddingClient(settings.voyage_api_key, settings.voyage_model)


def retriever_manager_dependency(request: Request) -> RetrieverManager:
    # DB 커넥션 풀은 app.py 의 lifespan 에서 만들어 app.state 에 둔다
    return RetrieverManager(
        ChunkRepository(request.app.state.db_pool), embedding_client_dependency(), settings.top_k
    )


@lru_cache
def chat_manager_dependency() -> ChatManager:
    return ChatManager(settings.owner_name, settings.claude_model, settings.anthropic_api_key)
