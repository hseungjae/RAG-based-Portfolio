"""질문을 넣으면 pgvector에서 어떤 섹션이 검색되는지 유사도와 함께 보여준다.

    python -m scripts.search "기능경기대회 성적은?"
    python -m scripts.search "지금 어디서 일해요?" "자격증 뭐 있어요?"
"""

import asyncio
import sys

from src.chunk.repository import ChunkRepository
from src.database.connection import create_pool
from src.embedding.client import EmbeddingClient
from src.retriever.manager import RetrieverManager
from src.settings import settings


async def main(questions: list[str]) -> None:
    pool = await create_pool(settings.database_url)
    try:
        manager = RetrieverManager(
            ChunkRepository(pool),
            EmbeddingClient(settings.gemini_api_key, settings.embedding_model, settings.embedding_dimension),
            settings.top_k,
        )
        for q in questions:
            print(f"\nQ. {q}")
            for i, r in enumerate(await manager.search(q), 1):
                print(f"  {i}. ({r.score:.2f}) {r.chunk.title}")
    finally:
        await pool.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('사용법: python -m scripts.search "질문" ["질문" ...]')
    asyncio.run(main(sys.argv[1:]))
