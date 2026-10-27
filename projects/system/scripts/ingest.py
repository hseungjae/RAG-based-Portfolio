"""dataset/profile 의 문서를 임베딩해서 pgvector에 저장한다.

자기소개 문서를 수정했다면 이 스크립트를 다시 실행하면 된다.

    python -m scripts.ingest
"""

import asyncio

from src.chunk.repository import ChunkRepository
from src.database.connection import create_pool
from src.embedding.client import EmbeddingClient
from src.retriever.manager import RetrieverManager
from src.settings import settings


async def main() -> None:
    pool = await create_pool(settings.database_url)
    try:
        manager = RetrieverManager(
            ChunkRepository(pool),
            EmbeddingClient(settings.gemini_api_key, settings.embedding_model, settings.embedding_dimension),
            settings.top_k,
        )
        n = await manager.ingest(settings.profile_dir)
        print(f"{n}개 청크를 저장했습니다. (model={settings.embedding_model})")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
