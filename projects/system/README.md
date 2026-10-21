# System (FastAPI RAG 백엔드)

## 디렉토리 구조

```bash
system/
├── run.py                  # FastAPI 애플리케이션 진입점
├── requirements.txt        # Python 의존성
├── .env.example            # 환경 변수 예시
├── dataset/
│   └── profile/            # 자기소개 원문 (마크다운, ## 섹션 단위로 청킹)
├── scripts/
│   └── ingest.py           # 문서 → 임베딩 → pgvector 저장
├── src/                    # 비즈니스 로직
│   ├── domain.py           # 도메인 객체 (Chunk, SearchResult)
│   ├── settings.py         # 환경 설정
│   ├── database/
│   │   └── connection.py   # asyncpg 커넥션 풀 (pgvector 타입 등록)
│   ├── embedding/
│   │   └── client.py       # Voyage AI 임베딩 (document / query)
│   ├── chunk/
│   │   ├── chunker.py      # 마크다운 → 청크 분할
│   │   └── repository.py   # profile_chunk 테이블 저장·유사도 검색
│   ├── retriever/
│   │   └── manager.py      # 적재(ingest)·검색 비즈니스 로직
│   └── chat/
│       ├── prompt.py       # 시스템 프롬프트, 문서 컨텍스트 구성
│       └── manager.py      # Gemini API 스트리밍 호출
└── webapp/                 # FastAPI 애플리케이션
    ├── app.py              # 앱 생성, DB 풀 lifespan, 정적 파일 등록
    ├── dependency.py       # Manager 의존성 주입
    ├── dto.py              # 요청/응답 DTO
    ├── rate_limit.py       # IP별 요청 제한
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
cp .env.example .env        # GEMINI_API_KEY, VOYAGE_API_KEY 입력
```

3. 자기소개 문서를 임베딩해서 DB에 저장 (문서를 고칠 때마다 다시 실행)

```bash
.venv/bin/python -m scripts.ingest
```

4. 서버 실행

```bash
.venv/bin/python run.py --reload
```

http://localhost:8000 접속. `GEMINI_API_KEY`가 없으면 검색된 원문을 그대로 보여주는 미리보기 모드로 동작합니다.

## API

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/config` | 이름, LLM 사용 가능 여부 |
| POST | `/api/chat` | `{question, history}` → SSE 스트림 (`sources` → `delta`… → `done`, 실패 시 `error`) |

## 배포

시작 명령을 `python run.py` 로 설정하고(`PORT` 환경 변수를 자동으로 읽습니다), 환경 변수에 `GEMINI_API_KEY`, `VOYAGE_API_KEY`, `DATABASE_URL`, `OWNER_NAME`을 넣으면 됩니다. DB는 pgvector 확장을 지원하는 PostgreSQL(예: Supabase, Neon, AWS RDS)을 쓰고, `deploy/local/postgresql/00-init.sql`을 한 번 실행해 테이블을 만드세요.
