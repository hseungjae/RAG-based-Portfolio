# 화면 구조와 동작

## 요청 흐름

```
브라우저 ─┬─ /, /assets/*  → nginx (빌드한 정적 파일)
          └─ /api/*        → nginx → System(FastAPI)
```

- 개발 중에는 nginx 대신 Vite 개발 서버가 `/api`를 `localhost:8000`으로 넘깁니다 (`vite.config.ts`).
- 배포에서는 nginx가 `/api`를 k3s의 `system` 서비스로 넘깁니다 (`nginx/nginx.conf`).
- 화면과 API가 같은 도메인이라 CORS 설정이 필요 없습니다.

## 컴포넌트

```
App (core/App.tsx)
└── ThemeProvider
    └── ChatbotPage         features/chatbot/presentation/pages/chatbot-page.tsx
        ├── Header          이름, 새 대화(대화 중일 때만), GitHub, Notion, ThemeToggle
        ├── main
        │   ├── EmptyChat   첫 화면 소개 (대화가 시작되면 감춤)
        │   └── MessageList 질문·답변 목록 (MessageItem, LoadingIndicator)
        └── ChatForm        입력창 + 보내기 버튼
```

상태는 `useChat` 훅 하나가 가지고 있고, `ChatbotPage`가 각 view에 내려 줍니다.

## 답변 스트리밍 (`useChat`, `chatbotRepository`, `core/network/stream-client.ts`)

1. 질문을 보내면 질문 메시지와 빈 답변 메시지를 먼저 추가합니다. 빈 답변은 점 3개 애니메이션으로 보입니다.
2. `/api/chat`의 SSE 응답을 읽으며 `event: delta`가 올 때마다 답변 내용을 이어 붙입니다.
3. 10초가 지나도 첫 글자가 없으면 "답변이 조금 늦어지고 있어요" 안내를 보여줍니다 (Gemini 무료 플랜 지연).
4. `event: error`나 HTTP 오류가 오면 답변 자리에 오류 문구를 빨간색으로 보여줍니다.
5. 끝난 질문·답변은 history에 쌓아 두고, 다음 질문 때 최근 6개만 함께 보내 후속 질문 맥락으로 씁니다.

## 입력창 (`ChatForm`)

| 동작 | 설명 |
|---|---|
| Enter | 보내기 (한글 조합 중에는 무시해 마지막 글자가 중복 전송되지 않게 함) |
| Shift + Enter | 줄바꿈 |
| 빈 입력창에서 Tab | 지금 보이는 예시 질문을 채워 넣음 |
| 예시 질문 | 3초마다 바뀜 (입력 중이거나 움직임 줄이기 설정이면 멈춤) |
| 높이 | 내용에 맞춰 늘어나고 140px을 넘으면 스크롤 |

## 테마 (`ThemeProvider`, `useTheme`)

- 시스템 → 라이트 → 다크 순서로 전환하고, 라이트·다크를 고르면 `localStorage.theme`에 저장합니다.
- `<html class="dark">`로 다크 테마를 켭니다 (Tailwind `darkMode: 'class'`).
- 색상은 `src/index.css`의 CSS 변수(shadcn/ui 규칙)로 정의합니다.
- `index.html`의 인라인 스크립트가 React보다 먼저 테마를 적용해 깜빡임을 막습니다.

## 캐시 (`nginx/nginx.conf`)

| 경로 | Cache-Control | 이유 |
|---|---|---|
| `/assets/*` | 1년, immutable | 파일 이름에 내용 해시가 붙어 바뀌면 주소도 바뀜 |
| `/index.html` 등 나머지 | no-cache | 새 배포의 JS/CSS 주소를 바로 받도록 매번 확인 |
