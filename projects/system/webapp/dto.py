from typing import Literal

from pydantic import BaseModel, Field

from src.domain import SearchResult


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequestDTO(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[Turn] = Field(default_factory=list, max_length=12)


class SourceDTO(BaseModel):
    title: str
    source: str
    score: float

    @staticmethod
    def from_domain(result: SearchResult) -> "SourceDTO":
        return SourceDTO(title=result.chunk.title, source=result.chunk.source,
                         score=round(result.score, 2))
