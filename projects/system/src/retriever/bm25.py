"""한국어용 BM25 검색.

한국어는 조사·어미가 붙어 단어 단위 매칭이 잘 안 되므로
'단어 토큰 + 글자 바이그램'을 함께 써서 점수를 계산한다.
외부 임베딩 API나 벡터 DB 없이 동작한다.
"""

import math
import re
from collections import Counter

from src.domain import Chunk, SearchResult

WORD_RE = re.compile(r"[0-9A-Za-z가-힣]+")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for word in WORD_RE.findall(text.lower()):
        tokens.append(word)
        if re.search(r"[가-힣]", word) and len(word) > 1:
            tokens.extend(word[i : i + 2] for i in range(len(word) - 1))
    return tokens


class BM25Index:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        # 섹션 제목도 검색 대상에 포함한다
        self.docs = [Counter(tokenize(f"{c.title}\n{c.content}")) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(len(self.docs), 1)
        df: Counter[str] = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int) -> list[SearchResult]:
        q = Counter(tokenize(query))
        results = []
        for chunk, doc, length in zip(self.chunks, self.docs, self.lengths):
            score = 0.0
            for term in q:
                tf = doc.get(term, 0)
                if tf:
                    norm = tf + self.k1 * (1 - self.b + self.b * length / self.avg_len)
                    score += self.idf[term] * tf * (self.k1 + 1) / norm
            if score > 0:
                results.append(SearchResult(chunk, score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:k]
