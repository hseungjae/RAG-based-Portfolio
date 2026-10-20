from pathlib import Path

from src.domain import SearchResult
from src.retriever.bm25 import BM25Index
from src.retriever.chunker import load_chunks


class RetrieverManager:
    def __init__(self, profile_dir: Path, top_k: int):
        self.index = BM25Index(load_chunks(profile_dir))
        self.top_k = top_k

    def search(self, question: str, prev_question: str = "") -> list[SearchResult]:
        # 후속 질문("그건 왜요?")도 잘 찾도록 직전 사용자 질문을 검색어에 합친다
        return self.index.search(f"{prev_question} {question}", k=self.top_k)
