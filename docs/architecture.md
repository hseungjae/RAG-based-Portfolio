# 아키텍처

## RAG 동작 흐름

```mermaid
sequenceDiagram
    participant Web as Web (채팅 화면)
    participant Router as webapp/routers/chat.py
    participant Retriever as RetrieverManager
    participant Embed as Gemini Embedding
    participant DB as PostgreSQL + pgvector
    participant Chat as ChatManager
    participant Gemini as Gemini API

    Web->>Router: POST /api/chat {question, history}
    Router->>Retriever: search(question, 직전 질문)
    Retriever->>Embed: 질문 임베딩 (task_type=RETRIEVAL_QUERY)
    Embed-->>Retriever: 1024차원 벡터
    Retriever->>DB: ORDER BY embedding <=> 질문벡터 LIMIT 4
    DB-->>Retriever: 코사인 유사도 상위 4개 청크
    Retriever-->>Router: 상위 4개 청크
    Router-->>Web: event: sources
    Router->>Chat: stream_answer(question, history, 청크)
    Chat->>Gemini: 시스템 프롬프트 + <documents> + 질문
    Gemini-->>Chat: 텍스트 스트림
    Chat-->>Router: 텍스트 조각
    Router-->>Web: event: delta (반복) → done
```

## 계층 구조

| 계층 | 위치 | 역할 |
|---|---|---|
| Router | `webapp/routers/` | 요청 검증(DTO), Manager 호출, SSE 응답 |
| Dependency | `webapp/dependency.py` | Manager 인스턴스 생성·주입 |
| Manager | `src/*/manager.py` | 적재·검색, 답변 생성 비즈니스 로직 |
| Repository | `src/chunk/repository.py` | pgvector 테이블 저장·유사도 검색 |
| Domain | `src/domain.py` | `Chunk`, `SearchResult` 데이터 클래스 |

## 설계 결정

- **pgvector 벡터 검색**: 문서 섹션과 질문을 Gemini 임베딩(`gemini-embedding-2-preview`, 1024차원)으로 변환하고, PostgreSQL의 pgvector로 코사인 유사도 검색을 합니다. 키워드가 달라도(예: "어디서 일해요?" ↔ "경력") 의미가 비슷하면 찾을 수 있습니다. 데이터가 적어도 HNSW 인덱스를 만들어 두어 문서가 늘어나도 그대로 쓸 수 있습니다.
- **문서/질문 임베딩 구분**: `task_type`을 문서는 `RETRIEVAL_DOCUMENT`, 질문은 `RETRIEVAL_QUERY`로 나눠 검색 품질을 높였습니다.
- **API 키 하나로 운영**: 답변 생성과 임베딩 모두 Gemini 무료 플랜을 써서 비용 없이 운영합니다. (처음엔 Voyage AI 임베딩을 썼지만, 결제수단 없이는 분당 3회로 제한돼 교체했습니다.)
- **적재와 서빙 분리**: 임베딩 저장은 `scripts/ingest.py`로 따로 실행해서, 서버를 띄울 때마다 임베딩 API를 호출하지 않습니다.
- **근거 기반 답변**: 문서에 없는 내용은 추측하지 않도록 지시하고, 답변마다 참고한 섹션을 화면에 표시합니다.
- **답변 프롬프트** (`src/chat/prompt.py`): 개발자 본인이 직접 답하는 느낌을 주도록 다섯 가지 지침을 둡니다.
  1. 페르소나: 문서 작성자 본인으로서 1인칭으로 답변
  2. 어조: 정중하고 친근한 존댓말, 모든 답변에서 같은 스타일 유지
  3. 길이: 100자 내외로 간결하게
  4. 제약: 검색된 문서의 정보만 사용
  5. 예외: 정보가 없거나 무관한 질문이면 정해진 안내 문장(`FALLBACK_ANSWER`)으로만 응답
- **후속 질문 처리**: 직전 사용자 질문을 검색어에 합쳐 "그 프로젝트에서 어려웠던 점은?" 같은 질문도 찾습니다.
- **비용 보호**: IP당 10분에 20회 요청 제한, 질문 길이 500자 제한.
