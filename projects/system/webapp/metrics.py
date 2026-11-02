"""Prometheus 지표. VictoriaMetrics 가 /metrics 를 15초마다 수집해 Grafana 에서 본다.

/metrics 는 nginx(react-app)가 넘기지 않으므로 클러스터 안에서만 접근할 수 있다.
"""

import time

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "http_requests_total", "HTTP 요청 수", ["method", "route", "status"]
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds", "응답 헤더를 보내기까지 걸린 시간", ["method", "route"]
)

LATENCY_BUCKETS = (0.5, 1, 2, 3, 5, 10, 20, 30, 60, 90, 120)
CHAT_QUESTIONS = Counter("chat_questions_total", "받은 질문 수")
CHAT_ANSWERS = Counter("chat_answers_total", "끝난 답변 수", ["result"])  # ok | unanswered | error | cancelled
CHAT_FIRST_TOKEN = Histogram(
    "chat_first_token_seconds", "질문부터 첫 답변 조각까지 걸린 시간", buckets=LATENCY_BUCKETS
)
CHAT_DURATION = Histogram(
    "chat_answer_seconds", "질문부터 답변이 끝날 때까지 걸린 시간", buckets=LATENCY_BUCKETS
)


async def http_metrics_middleware(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    # 경로 대신 라우트 템플릿을 라벨로 써서, 없는 주소를 마구 찔러도 시계열이 늘지 않게 한다
    route = request.scope.get("route")
    path = route.path if route is not None else "unmatched"
    if path != "/metrics":
        HTTP_REQUESTS.labels(request.method, path, response.status_code).inc()
        HTTP_DURATION.labels(request.method, path).observe(time.perf_counter() - started)
    return response


def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
