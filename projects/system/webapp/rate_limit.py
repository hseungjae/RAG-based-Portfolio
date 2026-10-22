import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from src.settings import settings

_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    # Cloudflare Tunnel을 거치면 모든 요청이 localhost(cloudflared)에서 온 것처럼 보이므로,
    # Cloudflare가 붙여주는 방문자 실제 IP 헤더를 먼저 쓴다.
    # 서버를 127.0.0.1에만 열어 두어야 외부에서 이 헤더를 위조할 수 없다.
    return request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")


def rate_limit(request: Request) -> None:
    """IP당 settings.rate_window초 동안 settings.rate_limit회까지만 허용한다."""
    ip = client_ip(request)
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > settings.rate_window:
        q.popleft()
    if len(q) >= settings.rate_limit:
        raise HTTPException(429, "질문이 너무 많아요. 잠시 후 다시 시도해주세요.")
    q.append(now)
