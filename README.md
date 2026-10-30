# RAG-based Portfolio

## 프로젝트 개요

RAG-based Portfolio는 자기소개 문서를 근거로 1인칭으로 답변하는 RAG(Retrieval-Augmented Generation) 챗봇입니다.
FastAPI 기반 RAG 서비스와 React 웹 화면으로 구성되며, k3s 클러스터에 배포해 [chat.sjhan.com](https://chat.sjhan.com)으로 공개합니다.

## 주요 구성 요소

* **System**: FastAPI 기반 RAG 서비스. PostgreSQL + pgvector로 자기소개 문서를 벡터 검색하고, Gemini API로 답변을 생성해 SSE로 스트리밍합니다.
* **React App**: 다크 모드를 지원하는 반응형 채팅 화면(React + TypeScript + Tailwind CSS + shadcn/ui). nginx가 빌드 결과를 제공하고 `/api` 요청은 System으로 넘깁니다.
* **Infra**: k3s(노드 2대)에 React App, System, PostgreSQL, Cloudflare Tunnel을 배포하고, 시크릿은 Sealed Secrets로 암호화해 관리합니다.

## 폴더 구조 및 주요 파일

```
RAG-based-Portfolio/
├── docs/               # 프로젝트 관련 문서 (아키텍처, 로컬 실행, 터널 공개)
├── deploy/             # 로컬 개발 환경
│   ├── local/          # pgvector PostgreSQL (docker compose)
│   └── tunnel/         # Cloudflare Tunnel 설정 예시 (Mac에서 공개할 때)
├── k3s/                # Kubernetes(k3s) 배포 매니페스트
│   ├── application/    # 네임스페이스, 챗봇 서버, 문서 적재 Job
│   ├── infra/          # PostgreSQL(pgvector), Cloudflare Tunnel
│   └── sealedsecret/   # Sealed Secrets로 암호화한 시크릿
└── projects/           # 서비스 코어 (System, React App)
    ├── system/         # FastAPI 기반 RAG 백엔드
    │   ├── dataset/    # 자기소개 원문 (마크다운)
    │   └── Dockerfile  # System(API) 이미지
    └── react-app/      # 채팅 화면 (React + Vite, nginx 이미지)
```

## 실행 방법

자세한 실행 방법은 각 폴더의 `README.md`와 문서를 참고하세요.

* **System (FastAPI)**: [`projects/system/README.md`](projects/system/README.md)
* **React App**: [`projects/react-app/README.md`](projects/react-app/README.md)
* **로컬 실행**: [`docs/local-guide.md`](docs/local-guide.md)
* **K3S (Kubernetes)**: [`k3s/README.md`](k3s/README.md)
* **아키텍처**: [`docs/architecture.md`](docs/architecture.md)
