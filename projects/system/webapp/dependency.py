from functools import lru_cache

from src.chat.manager import ChatManager
from src.retriever.manager import RetrieverManager
from src.settings import settings


@lru_cache
def retriever_manager_dependency() -> RetrieverManager:
    return RetrieverManager(settings.profile_dir, settings.top_k)


@lru_cache
def chat_manager_dependency() -> ChatManager:
    return ChatManager(settings.owner_name, settings.claude_model, settings.anthropic_api_key)
