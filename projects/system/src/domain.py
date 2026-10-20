from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: int
    source: str   # 원본 파일 이름
    title: str    # "문서 제목 > 섹션 제목"
    content: str


@dataclass
class SearchResult:
    chunk: Chunk
    score: float
