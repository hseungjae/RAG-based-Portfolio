import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from src.settings import settings

_hits: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    """IP당 settings.rate_window초 동안 settings.rate_limit회까지만 허용한다."""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > settings.rate_window:
        q.popleft()
    if len(q) >= settings.rate_limit:
        raise HTTPException(429, "질문이 너무 많아요. 잠시 후 다시 시도해주세요.")
    q.append(now)
