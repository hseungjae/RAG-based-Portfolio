from pathlib import Path

from src.chunk.chunker import load_chunks
from src.chunk.repository import ChunkRepository
from src.domain import SearchResult
from src.embedding.client import EmbeddingClient
from src.retriever.rerank import rerank

# 벡터 검색으로 넉넉히 뽑은 뒤 제목 키워드로 다시 정렬해서 top_k만 남긴다
CANDIDATES = 10


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
        if not prev_question:
            [embedding] = await self.embedder.embed([question], "query")
            return (await self._candidates(embedding, question))[: self.top_k]

        # 이전 질문을 합친 검색은 후속 질문("그건 왜요?")에 필요하지만, 주제가 바뀐 질문에서는
        # 이전 질문의 의미가 검색을 덮어버린다. 두 검색 결과를 번갈아 가며 섞어 둘 다 살린다.
        current_emb, combined_emb = await self.embedder.embed(
            [question, f"{prev_question}\n{question}"], "query"
        )
        current = await self._candidates(current_emb, question)
        combined = await self._candidates(combined_emb, question)
        merged: list[SearchResult] = []
        seen: set[int] = set()
        for pair in zip(current, combined):
            for r in pair:
                if r.chunk.chunk_id not in seen and len(merged) < self.top_k:
                    seen.add(r.chunk.chunk_id)
                    merged.append(r)
        return merged

    async def _candidates(self, embedding: list[float], question: str) -> list[SearchResult]:
        candidates = await self.repository.search_similar(embedding, CANDIDATES)
        # 가산점은 지금 질문의 단어로만 준다 (이전 질문 단어로 주면 주제가 바뀐 질문에서 엉뚱한 섹션이 올라온다)
        return rerank(question, candidates, CANDIDATES)
