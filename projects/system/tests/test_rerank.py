from src.domain import Chunk, SearchResult
from src.retriever.rerank import MAX_BONUS, TITLE_BONUS, rerank


def result(chunk_id: int, title: str, score: float) -> SearchResult:
    return SearchResult(Chunk(chunk_id, "doc.md", title, "내용"), score)


def scores(results: list[SearchResult]) -> list[tuple[int, float]]:
    return [(r.chunk.chunk_id, round(r.score, 4)) for r in results]


def test_title_keyword_moves_section_up():
    results = [result(0, "소개 > 취미", 0.80), result(1, "기술 > 자격증", 0.78)]

    # "자격증은" 처럼 조사가 붙어도 제목의 "자격증"과 맞는다
    ranked = rerank("자격증은 뭐가 있나요?", results, k=2)

    assert scores(ranked) == [(1, round(0.78 + TITLE_BONUS, 4)), (0, 0.80)]


def test_bonus_is_capped():
    results = [result(0, "프로젝트 > 쿠버네티스 모니터링 대시보드", 0.70)]

    ranked = rerank("쿠버네티스 모니터링 대시보드 프로젝트", results, k=1)

    assert scores(ranked) == [(0, round(0.70 + MAX_BONUS, 4))]


def test_stopwords_give_no_bonus():
    results = [result(0, "한승재 > 경험", 0.60), result(1, "소개 > 경력", 0.65)]

    # 이름과 "경험"은 거의 모든 질문에 들어가서 순위를 바꾸면 안 된다
    ranked = rerank("한승재 경험이 궁금해요", results, k=2)

    assert scores(ranked) == [(1, 0.65), (0, 0.60)]


def test_returns_at_most_k():
    results = [result(i, f"섹션 {i}", 0.9 - i * 0.1) for i in range(5)]

    assert [r.chunk.chunk_id for r in rerank("안녕하세요", results, k=3)] == [0, 1, 2]
