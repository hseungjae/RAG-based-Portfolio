"""검색 결과를 근거로 Claude 답변을 스트리밍한다."""

from collections.abc import AsyncIterator

import anthropic

from src.chat.prompt import build_system_prompt, build_user_message
from src.domain import SearchResult


class ChatManager:
    def __init__(self, owner: str, model: str, api_key: str | None):
        self.model = model
        self.system_prompt = build_system_prompt(owner)
        self.client = anthropic.AsyncAnthropic(api_key=api_key) if api_key else None

    @property
    def llm_enabled(self) -> bool:
        return self.client is not None

    async def stream_answer(
        self, question: str, history: list[dict], results: list[SearchResult]
    ) -> AsyncIterator[str]:
        """답변 텍스트 조각을 차례로 내보낸다. API 오류는 RuntimeError로 바꿔 올린다."""
        if self.client is None:
            # API 키 없이도 검색 결과는 확인할 수 있는 미리보기 모드
            preview = "\n\n".join(f"**{r.chunk.title}**\n{r.chunk.content}" for r in results[:2])
            yield "⚠️ API 키가 설정되지 않아 검색된 원문을 그대로 보여드려요.\n\n"
            yield preview or "관련 내용을 찾지 못했어요."
            return

        messages = [*history, {"role": "user", "content": build_user_message(question, results)}]
        try:
            async with self.client.beta.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=messages,
                # 짧은 Q&A라 낮은 effort로 충분하고 응답도 빠르다
                output_config={"effort": "low"},
                # 안전 분류기가 거절하면 서버가 다른 모델로 자동 재시도
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                final = await stream.get_final_message()
            if final.stop_reason == "refusal":
                yield "\n\n죄송해요, 이 질문에는 답변드리기 어려워요."
        except anthropic.RateLimitError as e:
            raise RuntimeError("지금 요청이 많아요. 잠시 후 다시 시도해주세요.") from e
        except anthropic.APIStatusError as e:
            raise RuntimeError(f"AI 서버 오류가 발생했어요. ({e.status_code})") from e
        except anthropic.APIConnectionError as e:
            raise RuntimeError("AI 서버에 연결하지 못했어요.") from e
