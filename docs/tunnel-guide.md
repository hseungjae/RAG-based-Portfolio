# Cloudflare Tunnel로 공개하기 (chat.sjhan.com)

이 Mac에서 실행 중인 서버(`localhost:8000`)를 Cloudflare Tunnel로 `https://chat.sjhan.com`에 연결합니다.
포트를 열거나 공유기 설정을 바꿀 필요가 없고, HTTPS 인증서도 Cloudflare가 자동으로 처리합니다.

```
방문자 → https://chat.sjhan.com → Cloudflare → (터널) → 이 Mac의 cloudflared → localhost:8000 (FastAPI) → Docker DB
```

> **주의:** 이 Mac이 꺼지거나 잠들면 사이트도 열리지 않습니다. 항상 켜 두는 서버가 필요해지면 클라우드 호스팅으로 옮기는 것을 고려하세요.

---

## 1. 처음 한 번만

### 1-1. cloudflared 설치

```bash
brew install cloudflared
```

### 1-2. Cloudflare 로그인

```bash
cloudflared tunnel login
```

브라우저가 열리면 Cloudflare에 로그인하고 **sjhan.com**을 선택해 승인합니다. `~/.cloudflared/cert.pem`이 생기면 성공입니다.

### 1-3. 터널 만들기

```bash
cloudflared tunnel create rag-portfolio
```

출력에 나오는 **터널 ID**(예: `6ff42ae2-765d-4adf-8112-31c55c1551ef`)를 기억해 두세요. `~/.cloudflared/<터널ID>.json` 인증 파일이 함께 생깁니다.

> 인증 파일(`*.json`)과 `cert.pem`은 비밀번호와 같습니다. GitHub나 채팅에 올리지 마세요.

### 1-4. 하위 도메인 연결

```bash
cloudflared tunnel route dns rag-portfolio chat.sjhan.com
```

Cloudflare DNS에 `chat` CNAME 레코드가 자동으로 만들어집니다. 터널은 주황 구름(Proxied) 상태여야 정상입니다.

### 1-5. 설정 파일 만들기

```bash
cp deploy/tunnel/config.example.yml ~/.cloudflared/config.yml
```

`~/.cloudflared/config.yml`을 열어 `<TUNNEL_ID>` 두 곳을 1-3의 터널 ID로 바꿉니다.

---

## 2. 매번 실행하는 순서

터미널 창 3개를 씁니다. (프로젝트 루트에서 시작)

**① DB**

```bash
cd deploy/local && docker compose up -d
```

**② 서버** — 외부 공개 시에는 반드시 `--host 127.0.0.1`로 실행합니다.

```bash
cd projects/system && .venv/bin/python run.py --host 127.0.0.1
```

**③ 터널**

```bash
cloudflared tunnel run rag-portfolio
```

`Registered tunnel connection`이 몇 줄 나오면 연결된 것입니다. 브라우저에서 https://chat.sjhan.com 에 접속해 확인하세요.

종료할 때는 ②와 ③ 터미널에서 **Ctrl + C**를 누릅니다.

### 왜 `--host 127.0.0.1`인가

- 서버는 Cloudflare가 붙여주는 `CF-Connecting-IP` 헤더로 방문자 IP를 구분해 요청 제한(IP당 10분에 20회)을 겁니다 (`webapp/rate_limit.py`).
- 서버를 `0.0.0.0`으로 열면 같은 와이파이의 다른 기기가 터널을 거치지 않고 직접 접속해 이 헤더를 마음대로 넣을 수 있습니다.
- `127.0.0.1`로 열면 이 Mac 안(cloudflared)에서만 접속할 수 있어 헤더를 위조할 수 없습니다.
- 같은 이유로 DB도 `127.0.0.1:5433`에만 열려 있습니다 (`deploy/local/docker-compose.yml`).

---

## 3. 켜 두는 동안 주의할 점

| 항목 | 설명 |
|---|---|
| Mac 잠자기 | 잠들면 사이트가 끊깁니다. 켜 두는 동안 `caffeinate -dims`를 다른 터미널에서 실행하면 잠들지 않습니다 (Ctrl + C로 해제) |
| 서버를 재시작하면 | 터널은 그대로 두면 됩니다. 서버가 다시 뜨면 자동으로 이어집니다 |
| 자기소개를 수정하면 | `cd projects/system && .venv/bin/python -m scripts.ingest` 후 바로 반영 (서버 재시작 불필요) |
| API 사용량 | 공개된 주소라 누구나 질문할 수 있습니다. IP당 요청 제한과 Gemini 무료 한도가 비용을 막아 줍니다 |

---

## 4. 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| chat.sjhan.com 접속 시 Cloudflare **502 / 1033** 오류 | 터널은 연결됐지만 8000 서버가 꺼져 있음, 또는 터널이 꺼져 있음 | ② 서버와 ③ 터널이 둘 다 실행 중인지 확인 |
| `cloudflared tunnel route dns` 실패 (레코드가 이미 있음) | Cloudflare DNS에 `chat` 레코드가 이미 있음 | Cloudflare 대시보드 **DNS → Records**에서 기존 `chat` 레코드를 지우고 다시 실행 |
| 답변이 한 번에 몰아서 나옴 | 중간에서 스트리밍이 버퍼링됨 | 서버가 `X-Accel-Buffering: no`, `Cache-Control: no-cache`를 보내고 있는지 확인 (기본 설정에 포함) |
| "질문이 너무 많아요"가 모두에게 뜸 | 서버가 방문자 IP를 구분하지 못함 | `webapp/rate_limit.py`의 `client_ip`가 `CF-Connecting-IP`를 읽는지 확인 |

---

## 5. 나중에 할 수 있는 것

- **Mac 로그인 시 터널 자동 실행:** `sudo cloudflared service install` (서비스로 등록. 해제는 `sudo cloudflared service uninstall`)
- **클라우드 호스팅으로 이전:** Mac을 켜 두지 않아도 되도록 서버를 클라우드에 배포하고, Cloudflare DNS의 `chat` 레코드를 새 서버 주소로 바꿉니다.
