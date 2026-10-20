# System (FastAPI RAG 백엔드)

## 디렉토리 구조

```bash
system/
├── run.py                  # FastAPI 애플리케이션 진입점
├── requirements.txt        # Python 의존성
├── .env.example            # 환경 변수 예시
├── dataset/
│   └── profile/            # 자기소개 원문 (마크다운, ## 섹션 단위로 청킹)
├── src/                    # 비즈니스 로직
│   ├── domain.py           # 도메인 객체 (Chunk, SearchResult)
│   ├── settings.py         # 환경 설정
│   ├── retriever/          # 문서 검색
│   │   ├── chunker.py      # 마크다운 → 청크 분할
│   │   ├── bm25.py         # 한국어 BM25 (단어 + 글자 바이그램)
│   │   └── manager.py      # 검색 비즈니스 로직
│   └── chat/               # 답변 생성
│       ├── prompt.py       # 시스템 프롬프트, 문서 컨텍스트 구성
│       └── manager.py      # Claude API 스트리밍 호출
└── webapp/                 # FastAPI 애플리케이션
    ├── app.py              # 앱 생성, 라우터·정적 파일 등록
    ├── dependency.py       # Manager 의존성 주입
    ├── dto.py              # 요청/응답 DTO
    ├── rate_limit.py       # IP별 요청 제한
    └── routers/
        └── chat.py         # /api/chat (SSE), /api/config
```

## 실행

```bash
cd projects/system
uv venv -p 3.12 && uv pip install -r requirements.txt
cp .env.example .env        # ANTHROPIC_API_KEY 입력
.venv/bin/python run.py --reload
```

http://localhost:8000 접속. API 키가 없으면 검색된 원문을 그대로 보여주는 미리보기 모드로 동작합니다.

## API

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/config` | 이름, LLM 사용 가능 여부 |
| POST | `/api/chat` | `{question, history}` → SSE 스트림 (`sources` → `delta`… → `done`, 실패 시 `error`) |

## 배포

시작 명령을 `python run.py` 로 설정하고(`PORT` 환경 변수를 자동으로 읽습니다), 환경 변수에 `ANTHROPIC_API_KEY`, `OWNER_NAME`을 넣으면 됩니다.
