import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.settings import settings
from webapp import rate_limit
from webapp.rate_limit import client_ip


def request(ip: str | None = None, host: str = "10.0.0.1") -> Request:
    headers = [(b"cf-connecting-ip", ip.encode())] if ip else []
    return Request({"type": "http", "headers": headers, "client": (host, 50000)})


def test_client_ip_prefers_cloudflare_header():
    assert client_ip(request(ip="1.2.3.4")) == "1.2.3.4"
    assert client_ip(request(host="10.0.0.9")) == "10.0.0.9"


def test_allows_again_after_window(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(settings, "rate_limit", 2)
    monkeypatch.setattr(settings, "rate_window", 60)

    rate_limit.rate_limit(request(ip="1.2.3.4"))
    rate_limit.rate_limit(request(ip="1.2.3.4"))
    with pytest.raises(HTTPException) as e:
        rate_limit.rate_limit(request(ip="1.2.3.4"))
    assert e.value.status_code == 429

    now[0] += 61
    rate_limit.rate_limit(request(ip="1.2.3.4"))
