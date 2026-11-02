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


@dataclass
class ChatLog:
    """질문 한 건의 처리 결과. Grafana 질문 통계 대시보드가 chat_log 테이블을 읽는다."""
    visitor: str                 # IP 해시 (방문자 수 집계용, 원본 IP는 저장하지 않음)
    question: str
    history_turns: int
    status: str                  # ok | error | cancelled
    duration_ms: int
    answer_chars: int = 0
    first_token_ms: int | None = None
    error: str | None = None
    sources: list[dict] | None = None   # [{"title": ..., "score": ...}]
