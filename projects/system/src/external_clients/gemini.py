from google import genai
from google.genai import types

# 무료 플랜은 가끔 503(과부하)을 주거나 응답 없이 멈추므로, 시간 제한과 재시도를 둔다.
# 429(무료 한도 초과)는 재시도해도 풀리지 않으니 재시도 대상에서 뺀다.
HTTP_OPTIONS = types.HttpOptions(
    timeout=60_000,  # ms. 무료 플랜이 붐빌 때는 첫 응답까지 30초 이상 걸리기도 한다
    retry_options=types.HttpRetryOptions(attempts=3, http_status_codes=[500, 502, 503, 504]),
)


def create_gemini_client(api_key: str | None) -> genai.Client | None:
    return genai.Client(api_key=api_key, http_options=HTTP_OPTIONS) if api_key else None
