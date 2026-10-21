from pathlib import Path

from src.chunk.chunker import load_chunks
from src.chunk.repository import ChunkRepository
from src.domain import SearchResult
from src.embedding.client import EmbeddingClient


class RetrieverManager:
    def __init__(self, repository: ChunkRepository, embedder: EmbeddingClient, top_k: int):
        self.repository = repository
        self.embedder = embedder
        self.top_k = top_k

    async def ingest(self, profile_dir: Path) -> int:
        """마크다운 문서를 청크로 나눠 임베딩한 뒤 pgvector에 저장한다."""
        chunks = load_chunks(profile_dir)
        # 섹션 제목도 함께 임베딩해야 "경력", "수상" 같은 질문이 잘 맞는다
        embeddings = await self.embedder.embed([f"{c.title}\n{c.content}" for c in chunks], "document")
        await self.repository.replace_all(chunks, embeddings)
        return len(chunks)

    async def search(self, question: str, prev_question: str = "") -> list[SearchResult]:
        # 후속 질문("그건 왜요?")도 잘 찾도록 직전 사용자 질문을 검색어에 합친다
        query = f"{prev_question}\n{question}".strip()
        [query_embedding] = await self.embedder.embed([query], "query")
        return await self.repository.search_similar(query_embedding, self.top_k)
