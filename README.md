# RAG-based Portfolio

자기소개 문서를 검색해서, 그 내용만 근거로 Gemini가 답변하는 RAG 챗봇 포트폴리오입니다.

## 폴더 구조

```
RAG-based Portfolio/
├── deploy/
│   ├── local/            # pgvector PostgreSQL (docker compose)
│   └── tunnel/           # Cloudflare Tunnel 설정 예시
├── docs/                 # 설계 문서
│   ├── architecture.md   # RAG 동작 흐름과 계층 구조
│   ├── local-guide.md    # 로컬 실행, 데이터 적재, 확인 명령어
│   └── tunnel-guide.md   # Cloudflare Tunnel로 chat.sjhan.com 공개
└── projects/
    ├── system/           # FastAPI 기반 RAG 백엔드
    └── web/              # 채팅 화면 (HTML / CSS / JS)
```

## 실행 방법

처음부터 실행하는 전체 순서와 확인 명령어는 **[docs/local-guide.md](docs/local-guide.md)**, Cloudflare Tunnel로 chat.sjhan.com에 공개하는 방법은 **[docs/tunnel-guide.md](docs/tunnel-guide.md)** 에 정리돼 있습니다.

각 구성 요소의 상세 설명:
- **DB (pgvector)**: [deploy/local/README.md](deploy/local/README.md)
- **System (FastAPI)**: [projects/system/README.md](projects/system/README.md)
- **Web**: 백엔드 서버가 `projects/web`을 함께 제공하므로 따로 실행할 필요가 없습니다.

## 자기소개 내용 수정

`projects/system/dataset/profile/` 안의 마크다운 파일을 수정한 뒤 `projects/system`에서 `python -m scripts.ingest`를 실행하면 임베딩이 다시 저장됩니다.

| 파일 | 내용 |
|---|---|
| `01_about.md` | 한승재는 누구인가 |
| `02_skills_competition.md` | 기능경기대회 |
| `03_projects.md` | 프로젝트 |
