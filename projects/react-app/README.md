# React App - Feature-First 구조 기반 챗봇 화면

## 프로젝트 개요

자기소개 RAG 챗봇의 채팅 화면입니다. React + TypeScript + Vite로 만들고, 스타일은 Tailwind CSS와 shadcn/ui 규칙을 따릅니다.
Feature-First 구조로 기능별 코드를 모으고, 백엔드와의 통신은 Nginx의 `/api` 프록시를 거칩니다.

---

## 프로젝트 구조

```plaintext
react-app/
├── docs/                  # 화면 구조와 동작 설명
├── nginx/
│   └── nginx.conf         # 정적 파일 제공 + /api 프록시 (SSE 버퍼링 끔)
├── public/                # favicon
├── src/
│   ├── components/        # 공통 컴포넌트
│   │   ├── ui/            # shadcn/ui 컴포넌트 (button, theme-provider)
│   │   ├── theme-toggle.tsx
│   │   └── index.ts
│   ├── core/              # 핵심 로직 (진입점, 네트워크, 상수, 유틸리티)
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── constants/     # API 주소, 외부 링크
│   │   ├── network/       # fetch 기반 JSON 클라이언트, SSE 스트리밍 클라이언트
│   │   └── utils/         # cn(), 마크다운 렌더러
│   ├── features/          # 기능별 모듈
│   │   └── chatbot/       # 챗봇 페이지와 대화 관리
│   ├── hooks/             # 공통 훅
│   └── index.css          # Tailwind CSS 설정, 라이트/다크 색상 토큰
├── Dockerfile             # pnpm 빌드 → Nginx 이미지
├── components.json        # shadcn/ui 설정
├── eslint.config.js
├── index.html
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
└── vite.config.ts         # @ 경로 별칭, 개발용 /api 프록시
```

---

## 주요 디렉터리 설명

### 1. **`features`**

각 기능은 다음 구조를 따릅니다.

```plaintext
features/
└── chatbot/
    ├── data/
    │   ├── dto/            # API 요청·응답 타입 (chat-query-dto, config-dto)
    │   └── repositories/   # API 호출 (chatbot-repository)
    ├── domain/
    │   ├── models/         # 화면에서 쓰는 모델 (message)
    │   └── use-cases/      # 상태와 동작을 담은 훅 (use-chat, use-config)
    ├── presentation/
    │   ├── pages/          # chatbot-page
    │   └── views/          # header, empty-chat, message-list, message-item, loading-indicator, chat-form
    └── index.ts
```

### 2. **`core`**

- `constants`: API 주소(`/api`), 외부 링크
- `network`: `http-client.ts`(JSON 요청, 오류 문구 추출), `stream-client.ts`(SSE 응답을 이벤트 단위로 읽음)
- `utils`: `cn()`(shadcn/ui), 굵게·목록·문단만 지원하는 마크다운 렌더러

### 3. **`components`**

여러 기능에서 재사용하는 UI 컴포넌트입니다. shadcn/ui 컴포넌트를 더 쓰려면 `pnpm dlx shadcn@latest add <컴포넌트>`로 `src/components/ui/`에 추가합니다.

---

## 네트워크 구조

```
React → chatbotRepository → (개발: Vite / 배포: Nginx) /api 프록시 → System(FastAPI) → SSE 응답
```

- API는 항상 화면과 같은 origin의 `/api`로 부르므로 CORS 설정이 필요 없습니다.
- 개발 중에는 `vite.config.ts`가 `/api`를 `http://localhost:8000`으로 넘깁니다.
- 배포에서는 `nginx/nginx.conf`가 `/api`를 k3s의 `system` 서비스로 넘깁니다.

---

## 실행

System 서버(`localhost:8000`)를 먼저 띄운 뒤 실행합니다. ([projects/system/README.md](../system/README.md))
pnpm은 `package.json`의 `packageManager`와 같은 버전(10.23.0)을 씁니다.

```bash
npm install -g pnpm@10.23.0   # 처음 한 번만
cd projects/react-app
pnpm install
pnpm dev                      # http://localhost:5173
```

| 명령 | 설명 |
|---|---|
| `pnpm dev` | 개발 서버 |
| `pnpm build` | 타입 검사 후 `dist/`에 빌드 |
| `pnpm preview` | 빌드 결과 미리보기 (`localhost:4173`) |
| `pnpm lint` | ESLint |

## 배포

```bash
docker build -t react-app:latest projects/react-app
```

k3s 배포는 [k3s/README.md](../../k3s/README.md), 화면 동작은 [docs/architecture.md](docs/architecture.md)를 참고하세요.
