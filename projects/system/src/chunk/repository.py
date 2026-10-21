import asyncpg
import numpy as np

from src.domain import Chunk, SearchResult


class ChunkRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def replace_all(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """자기소개 문서는 양이 적으므로 매번 전체를 지우고 다시 넣는다."""
        rows = [(c.chunk_id, c.source, c.title, c.content, np.array(e, dtype=np.float32))
                for c, e in zip(chunks, embeddings)]
        async with self.pool.acquire() as conn, conn.transaction():
            await conn.execute("TRUNCATE profile_chunk")
            await conn.executemany(
                "INSERT INTO profile_chunk (chunk_id, source, title, content, embedding)"
                " VALUES ($1, $2, $3, $4, $5)",
                rows,
            )

    async def search_similar(self, query_embedding: list[float], k: int) -> list[SearchResult]:
        # <=> 는 코사인 거리. 1 - 거리 = 코사인 유사도
        try:
            rows = await self.pool.fetch(
                "SELECT chunk_id, source, title, content, 1 - (embedding <=> $1) AS score"
                " FROM profile_chunk ORDER BY embedding <=> $1 LIMIT $2",
                np.array(query_embedding, dtype=np.float32), k,
            )
        except (asyncpg.PostgresError, OSError) as e:
            raise RuntimeError("문서 DB에서 검색하지 못했어요.") from e
        return [
            SearchResult(Chunk(r["chunk_id"], r["source"], r["title"], r["content"]), float(r["score"]))
            for r in rows
        ]

    async def count(self) -> int:
        return await self.pool.fetchval("SELECT count(*) FROM profile_chunk")
