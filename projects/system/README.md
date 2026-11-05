# System (FastAPI RAG 백엔드)

## 디렉토리 구조

```bash
system/
├── run.py                  # FastAPI 애플리케이션 진입점
├── requirements.txt        # Python 의존성
├── requirements-dev.txt    # 테스트용 의존성 (pytest)
├── pytest.ini
├── .env.example            # 환경 변수 예시
├── dataset/
│   └── profile/            # 자기소개 원문 (마크다운, ## 섹션 단위로 청킹)
├── scripts/
│   ├── ingest.py           # 문서 → 임베딩 → pgvector 저장
│   └── search.py           # 질문을 넣어 검색 결과·유사도 확인
├── src/                    # 비즈니스 로직
│   ├── domain.py           # 도메인 객체 (Chunk, SearchResult, ChatLog)
│   ├── settings.py         # 환경 설정
│   ├── database/
│   │   └── connection.py   # asyncpg 커넥션 풀 (pgvector 타입 등록)
│   ├── external_clients/
│   │   └── gemini.py       # Gemini 클라이언트 (시간 제한, 503 재시도)
│   ├── embedding/
│   │   └── client.py       # Gemini 임베딩 (document / query, 1024차원)
│   ├── chunk/
│   │   ├── chunker.py      # 마크다운 → 청크 분할
│   │   └── repository.py   # profile_chunk 테이블 저장·유사도 검색
│   ├── retriever/
│   │   └── manager.py      # 적재(ingest)·검색 비즈니스 로직
│   ├── chat/
│   │   ├── prompt.py       # 시스템 프롬프트, 문서 컨텍스트 구성
│   │   └── manager.py      # Gemini API 스트리밍 호출
│   └── chat_log/
│       └── repository.py   # 질문 기록(chat_log 테이블) 생성·저장
├── tests/                  # pytest (가짜 DB·Gemini로 실행, 시크릿 불필요)
└── webapp/                 # FastAPI 애플리케이션
    ├── app.py              # 앱 생성, DB 풀 lifespan
    ├── dependency.py       # Manager 의존성 주입
    ├── dto.py              # 요청/응답 DTO
    ├── rate_limit.py       # IP별 요청 제한
    ├── metrics.py          # Prometheus 지표 (/metrics)
    └── routers/
        └── chat.py         # /api/chat (SSE), /api/config
```

## 실행

1. pgvector DB 실행 ([deploy/local/README.md](../../deploy/local/README.md))

```bash
cd deploy/local && docker compose up -d
```

2. 의존성 설치와 환경 변수 설정

```bash
cd projects/system
uv venv -p 3.12 && uv pip install -r requirements.txt
cp .env.example .env        # GEMINI_API_KEY 입력
```

3. 자기소개 문서를 임베딩해서 DB에 저장 (문서를 고칠 때마다 다시 실행)

```bash
.venv/bin/python -m scripts.ingest
```

4. 서버 실행

```bash
.venv/bin/python run.py --reload
```

API는 http://localhost:8000/api 에서 동작합니다. 채팅 화면은 [`projects/react-app`](../react-app/README.md)에서 `pnpm dev`로 띄웁니다.

## 테스트

DB와 Gemini를 가짜 객체로 바꿔 끼워 실행하므로 `.env`나 DB 없이 돌아갑니다.

```bash
uv pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

| 파일 | 확인하는 것 |
|---|---|
| `test_chat_api.py` | `/api/chat` SSE 순서, `chat_log` 저장(ok·unanswered·error), 요청 검증, 요청 제한, 지표 |
| `test_retriever.py` | 검색 결과 개수, 후속 질문 검색 섞기, 적재 시 제목+본문 임베딩 |
| `test_rerank.py` | 섹션 제목 가산점, 상한, 불용어 |
| `test_chunker.py` | `##` 섹션 분할, 실제 자기소개 문서 파싱 |
| `test_prompt.py` | 거절 문장 판별, 문서 컨텍스트 구성 |
| `test_rate_limit.py` | Cloudflare IP 헤더, 시간 창이 지나면 다시 허용 |

GitHub에 push 하거나 PR을 올리면 [CI](../../.github/workflows/ci.yml)가 같은 테스트를 돌립니다.

## API

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/config` | 이름, LLM 사용 가능 여부 |
| POST | `/api/chat` | `{question, history}` → SSE 스트림 (`sources` → `delta`… → `done`, 실패 시 `error`) |
| GET | `/metrics` | Prometheus 지표 (요청 수·지연, 질문·답변 수). nginx 가 넘기지 않아 클러스터 안에서만 접근 |

질문마다 결과(정상·실패·중간 취소), 소요 시간, 근거 섹션을 `chat_log` 테이블에 저장합니다. 테이블은 서버가 시작할 때 없으면 만듭니다. Grafana 질문 통계 대시보드가 이 테이블을 읽습니다 ([k3s/README.md](../../k3s/README.md) 7장).

## 배포

시작 명령을 `python run.py` 로 설정하고(`PORT` 환경 변수를 자동으로 읽습니다), 환경 변수에 `GEMINI_API_KEY`, `DATABASE_URL`, `OWNER_NAME`을 넣으면 됩니다. DB는 pgvector 확장을 지원하는 PostgreSQL(예: Supabase, Neon, AWS RDS)을 쓰고, `deploy/local/postgresql/00-init.sql`을 한 번 실행해 테이블을 만드세요.
