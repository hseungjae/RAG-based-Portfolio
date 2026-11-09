"""Gemini 임베딩 클라이언트.

gemini-embedding-2는 task_type을 받지 않으므로 용도를 텍스트 앞 문구로 알려 준다.
문서는 적재할 때 "title: ... | text: ..." 형식으로 넘어오고, 질문에는 검색용 문구를 붙인다.
"""

from typing import Literal

from google.genai import errors, types

from src.external_clients.gemini import create_gemini_client

QUERY_PREFIX = "task: search result | query: "


class EmbeddingClient:
    def __init__(self, api_key: str | None, model: str, dimension: int):
        self.model = model
        self.dimension = dimension
        self.client = create_gemini_client(api_key)

    async def embed(self, texts: list[str], input_type: Literal["document", "query"]) -> list[list[float]]:
        if self.client is None:
            raise RuntimeError("GEMINI_API_KEY가 설정되지 않아 검색을 할 수 없어요.")
        if input_type == "query":
            texts = [QUERY_PREFIX + t for t in texts]
        # 문자열 리스트를 그대로 넘기면 하나의 벡터로 합쳐지므로 텍스트마다 Content로 감싼다
        contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]
        config = types.EmbedContentConfig(output_dimensionality=self.dimension)
        try:
            result = await self.client.aio.models.embed_content(
                model=self.model, contents=contents, config=config,
            )
        except errors.APIError as e:
            # 상태 코드를 남겨야 로그에서 모델 종료(404)·요청 형식(400)·한도 초과(429)를 구분할 수 있다
            raise RuntimeError(f"임베딩 서버 오류로 검색하지 못했어요. ({e.code})") from e
        except TimeoutError as e:
            raise RuntimeError("임베딩 서버 오류로 검색하지 못했어요.") from e
        return [e.values for e in result.embeddings]
