"""검색 결과를 근거로 Gemini 답변을 스트리밍한다."""

from collections.abc import AsyncIterator

from google.genai import errors, types

from src.chat.prompt import build_system_prompt, build_user_message
from src.domain import SearchResult
from src.external_clients.gemini import create_gemini_client


class ChatManager:
    def __init__(self, owner: str, model: str, api_key: str | None):
        self.model = model
        self.system_prompt = build_system_prompt(owner)
        self.client = create_gemini_client(api_key)

    async def stream_answer(
        self, question: str, history: list[dict], results: list[SearchResult]
    ) -> AsyncIterator[str]:
        """답변 텍스트 조각을 차례로 내보낸다. API 오류는 RuntimeError로 바꿔 올린다."""
        if self.client is None:
            raise RuntimeError("GEMINI_API_KEY가 설정되지 않았어요.")
        # Gemini는 assistant 대신 model 역할 이름을 쓴다
        contents = [
            types.Content(role="model" if t["role"] == "assistant" else "user",
                          parts=[types.Part(text=t["content"])])
            for t in history
        ]
        contents.append(types.Content(role="user",
                                      parts=[types.Part(text=build_user_message(question, results))]))
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            max_output_tokens=2048,
        )

        answered = False
        try:
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model, contents=contents, config=config,
            )
            async for chunk in stream:
                if chunk.text:
                    answered = True
                    yield chunk.text
        except TimeoutError as e:
            raise RuntimeError("AI 서버 응답이 늦어요. 잠시 후 다시 시도해주세요.") from e
        except errors.APIError as e:
            if e.code == 429:
                raise RuntimeError("오늘 사용할 수 있는 무료 요청을 다 썼거나 요청이 많아요. 잠시 후 다시 시도해주세요.") from e
            if e.code in (400, 401, 403) and "API key" in (e.message or ""):
                raise RuntimeError("Gemini API 키가 올바르지 않아요. 서버 설정을 확인해주세요.") from e
            raise RuntimeError(f"AI 서버 오류가 발생했어요. ({e.code})") from e
        if not answered:
            # 안전 필터 등으로 답변이 비어 있는 경우
            yield "죄송해요, 이 질문에는 답변드리기 어려워요."
