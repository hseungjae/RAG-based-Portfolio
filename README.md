# RAG-based Portfolio

한승재의 자기소개 문서를 검색해서, 그 내용만 근거로 Gemini가 답변하는 RAG 챗봇 포트폴리오입니다.

## 폴더 구조

```
RAG-based Portfolio/
├── deploy/
│   └── local/            # pgvector PostgreSQL (docker compose)
├── docs/                 # 설계 문서
│   └── architecture.md   # RAG 동작 흐름과 계층 구조
└── projects/
    ├── system/           # FastAPI 기반 RAG 백엔드
    └── web/              # 채팅 화면 (HTML / CSS / JS)
```

## 실행 방법

자세한 실행 방법은 각 폴더의 README를 참고하세요.
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
