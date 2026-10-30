import json
import logging
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from src.chat.manager import ChatManager
from src.retriever.manager import RetrieverManager
from src.settings import settings
from webapp.dependency import chat_manager_dependency, retriever_manager_dependency
from webapp.dto import ChatRequestDTO, SourceDTO
from webapp.rate_limit import client_ip, rate_limit

router = APIRouter(prefix="/api", tags=["Chat"])
logger = logging.getLogger("rag.chat")


def sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/config")
async def config():
    return {"owner": settings.owner_name}


@router.post("/chat", dependencies=[Depends(rate_limit)])
async def chat(
    req: ChatRequestDTO,
    request: Request,
    retriever: RetrieverManager = Depends(retriever_manager_dependency),
    chat: ChatManager = Depends(chat_manager_dependency),
):
    prev_question = next((t.content for t in reversed(req.history) if t.role == "user"), "")
    history = [t.model_dump() for t in req.history]
    ip = client_ip(request)
    # 방문자가 어떤 질문을 했는지 남긴다. 줄바꿈은 한 줄 로그가 되도록 \n 으로 바꾼다
    logger.info("질문 ip=%s history=%d q=%s", ip, len(history), json.dumps(req.question, ensure_ascii=False))

    async def stream():
        started = time.monotonic()
        answer_len = 0
        try:
            results = await retriever.search(req.question, prev_question)
            yield sse("sources", [SourceDTO.from_domain(r).model_dump() for r in results])
            async for text in chat.stream_answer(req.question, history, results):
                answer_len += len(text)
                yield sse("delta", text)
            sources = ", ".join(f"{r.chunk.title}({r.score:.2f})" for r in results)
            logger.info("답변 ip=%s %.1fs %d자 sources=[%s]", ip, time.monotonic() - started, answer_len, sources)
        except RuntimeError as e:
            logger.warning("실패 ip=%s %.1fs error=%s", ip, time.monotonic() - started, e)
            yield sse("error", str(e))
        yield sse("done", {})

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
