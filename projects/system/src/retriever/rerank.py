"""벡터 검색 후보를 섹션 제목 키워드로 다시 정렬한다 (하이브리드 검색).

임베딩 유사도는 섹션끼리 점수 차이가 작아서, "경력"처럼 짧은 질문은 내용이 긴 섹션의
의미에 묻혀 순위가 밀리기 쉽다. 질문의 단어가 섹션 제목에 그대로 들어 있으면 가산점을 준다.
"""

import re

from src.domain import SearchResult

TITLE_BONUS = 0.05   # 제목에 맞는 단어 하나당 가산점
MAX_BONUS = 0.10     # 가산점 상한
# 질문에 흔히 들어가지만 의미를 구분하지 못하는 단어
STOPWORDS = {"어떤", "어떻게", "무엇", "뭐예요", "뭔가요", "있어요", "있나요", "했어요", "했나요",
             "알려줘", "알려주세요", "궁금해요", "한승재", "승재", "그럼", "그거", "그건", "경험"}


def _keywords(question: str) -> list[str]:
    words = re.findall(r"[0-9A-Za-z가-힣]+", question)
    return [w for w in words if len(w) >= 2 and w not in STOPWORDS]


def _matches(word: str, title: str) -> bool:
    # 조사가 붙은 단어("경력이", "자격증은")도 맞도록 앞에서부터 2글자까지 줄여 가며 비교
    for end in range(len(word), 1, -1):
        stem = word[:end]
        if stem in STOPWORDS:
            return False
        if stem in title:
            return True
    return False


def rerank(question: str, results: list[SearchResult], k: int) -> list[SearchResult]:
    keywords = _keywords(question)
    rescored = []
    for r in results:
        hits = sum(_matches(w, r.chunk.title) for w in keywords)
        rescored.append(SearchResult(r.chunk, r.score + min(hits * TITLE_BONUS, MAX_BONUS)))
    rescored.sort(key=lambda r: r.score, reverse=True)
    return rescored[:k]
