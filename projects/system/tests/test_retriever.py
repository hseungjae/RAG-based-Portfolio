import asyncio

from src.domain import Chunk, SearchResult
from src.retriever.manager import CANDIDATES, RetrieverManager


def result(chunk_id: int, score: float) -> SearchResult:
    return SearchResult(Chunk(chunk_id, "doc.md", f"문서 > 섹션{chunk_id}", "내용"), score)


class FakeEmbedder:
    """i번째 문장을 [i] 벡터로 바꾼다. 어떤 문장을 임베딩했는지 기록한다."""

    def __init__(self):
        self.calls: list[tuple[list[str], str]] = []

    async def embed(self, texts: list[str], task: str) -> list[list[float]]:
        self.calls.append((texts, task))
        return [[float(i)] for i in range(len(texts))]


class FakeRepository:
    def __init__(self, by_embedding: dict[float, list[SearchResult]] | None = None):
        self.by_embedding = by_embedding or {}
        self.saved = None

    async def search_similar(self, embedding: list[float], limit: int) -> list[SearchResult]:
        assert limit == CANDIDATES
        return self.by_embedding[embedding[0]]

    async def replace_all(self, chunks, embeddings) -> None:
        self.saved = (chunks, embeddings)


def test_search_returns_top_k():
    embedder = FakeEmbedder()
    repo = FakeRepository({0.0: [result(i, 0.9 - i * 0.1) for i in range(5)]})

    found = asyncio.run(RetrieverManager(repo, embedder, top_k=3).search("안녕하세요"))

    assert embedder.calls == [(["안녕하세요"], "query")]
    assert [r.chunk.chunk_id for r in found] == [0, 1, 2]


def test_follow_up_mixes_current_and_combined_search():
    embedder = FakeEmbedder()
    # 0번 벡터: 지금 질문만, 1번 벡터: 이전 질문 + 지금 질문
    repo = FakeRepository({
        0.0: [result(1, 0.9), result(2, 0.8), result(3, 0.7)],
        1.0: [result(2, 0.9), result(4, 0.8), result(5, 0.7)],
    })

    found = asyncio.run(RetrieverManager(repo, embedder, top_k=3).search("그건 왜요?", "경력은?"))

    assert embedder.calls == [(["그건 왜요?", "경력은?\n그건 왜요?"], "query")]
    # 두 결과를 번갈아 섞고, 겹치는 2번은 한 번만 넣는다
    assert [r.chunk.chunk_id for r in found] == [1, 2, 4]


def test_ingest_embeds_title_with_content(tmp_path):
    (tmp_path / "01_about.md").write_text("# 소개\n## 경력\n클라우드 엔지니어\n", encoding="utf-8")
    embedder, repo = FakeEmbedder(), FakeRepository()

    count = asyncio.run(RetrieverManager(repo, embedder, top_k=3).ingest(tmp_path))

    assert count == 1
    assert embedder.calls == [(["소개 > 경력\n클라우드 엔지니어"], "document")]
    chunks, embeddings = repo.saved
    assert [c.title for c in chunks] == ["소개 > 경력"]
    assert embeddings == [[0.0]]
