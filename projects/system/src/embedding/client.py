"""Gemini 임베딩 클라이언트.

문서와 질문은 task_type을 다르게 줘야 검색 품질이 좋아진다.
"""

from typing import Literal

from google.genai import errors, types

from src.external_clients.gemini import create_gemini_client

TASK_TYPES = {"document": "RETRIEVAL_DOCUMENT", "query": "RETRIEVAL_QUERY"}


class EmbeddingClient:
    def __init__(self, api_key: str | None, model: str, dimension: int):
        self.model = model
        self.dimension = dimension
        self.client = create_gemini_client(api_key)

    async def embed(self, texts: list[str], input_type: Literal["document", "query"]) -> list[list[float]]:
        if self.client is None:
            raise RuntimeError("GEMINI_API_KEY가 설정되지 않아 검색을 할 수 없어요.")
        # 문자열 리스트를 그대로 넘기면 하나의 벡터로 합쳐지므로 텍스트마다 Content로 감싼다
        contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]
        config = types.EmbedContentConfig(
            task_type=TASK_TYPES[input_type], output_dimensionality=self.dimension,
        )
        try:
            result = await self.client.aio.models.embed_content(
                model=self.model, contents=contents, config=config,
            )
        except (errors.APIError, TimeoutError) as e:
            raise RuntimeError("임베딩 서버 오류로 검색하지 못했어요.") from e
        return [e.values for e in result.embeddings]
