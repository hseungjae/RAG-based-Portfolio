import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.chat.manager import ChatManager
from src.retriever.manager import RetrieverManager
from src.settings import settings
from webapp.dependency import chat_manager_dependency, retriever_manager_dependency
from webapp.dto import ChatRequestDTO, SourceDTO
from webapp.rate_limit import rate_limit

router = APIRouter(prefix="/api", tags=["Chat"])


def sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/config")
async def config():
    return {"owner": settings.owner_name}


@router.post("/chat", dependencies=[Depends(rate_limit)])
async def chat(
    req: ChatRequestDTO,
    retriever: RetrieverManager = Depends(retriever_manager_dependency),
    chat: ChatManager = Depends(chat_manager_dependency),
):
    prev_question = next((t.content for t in reversed(req.history) if t.role == "user"), "")
    history = [t.model_dump() for t in req.history]

    async def stream():
        try:
            results = await retriever.search(req.question, prev_question)
            yield sse("sources", [SourceDTO.from_domain(r).model_dump() for r in results])
            async for text in chat.stream_answer(req.question, history, results):
                yield sse("delta", text)
        except RuntimeError as e:
            yield sse("error", str(e))
        yield sse("done", {})

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
