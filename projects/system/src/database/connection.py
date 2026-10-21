import asyncpg
from pgvector.asyncpg import register_vector


async def create_pool(database_url: str) -> asyncpg.Pool:
    # 커넥션마다 pgvector 타입을 등록해야 list[float] ↔ vector 변환이 된다
    return await asyncpg.create_pool(database_url, min_size=1, max_size=5, init=register_vector)
