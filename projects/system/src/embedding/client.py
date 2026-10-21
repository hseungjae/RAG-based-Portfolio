"""Voyage AI 임베딩 클라이언트.

문서와 질문은 input_type을 다르게 줘야 검색 품질이 좋아진다.
"""

from typing import Literal

import voyageai


class EmbeddingClient:
    def __init__(self, api_key: str | None, model: str):
        self.model = model
        self.client = voyageai.AsyncClient(api_key=api_key, max_retries=2) if api_key else None

    async def embed(self, texts: list[str], input_type: Literal["document", "query"]) -> list[list[float]]:
        if self.client is None:
            raise RuntimeError("VOYAGE_API_KEY가 설정되지 않아 검색을 할 수 없어요.")
        try:
            result = await self.client.embed(texts, model=self.model, input_type=input_type)
        except voyageai.error.VoyageError as e:
            raise RuntimeError("임베딩 서버 오류로 검색하지 못했어요.") from e
        return result.embeddings
