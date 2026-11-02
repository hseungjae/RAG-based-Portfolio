import asyncio
import hashlib
import json
import logging
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from src.chat.manager import ChatManager
from src.chat.prompt import is_unanswered
from src.chat_log.repository import ChatLogRepository
from src.domain import ChatLog
from src.retriever.manager import RetrieverManager
from src.settings import settings
from webapp.dependency import chat_manager_dependency, retriever_manager_dependency
from webapp.dto import ChatRequestDTO, SourceDTO
from webapp.metrics import CHAT_ANSWERS, CHAT_DURATION, CHAT_FIRST_TOKEN, CHAT_QUESTIONS
from webapp.rate_limit import client_ip, rate_limit

router = APIRouter(prefix="/api", tags=["Chat"])
logger = logging.getLogger("rag.chat")
# 질문 기록 저장은 답변 응답과 따로 돌린다. 태스크가 중간에 지워지지 않도록 참조를 잡아 둔다
_background: set[asyncio.Task] = set()


def visitor_id(ip: str) -> str:
    # 방문자 수 집계용. 원본 IP는 DB에 저장하지 않는다
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


async def save_log(repo: ChatLogRepository, log: ChatLog) -> None:
    try:
        await repo.insert(log)
    except Exception:
        # 기록 실패가 답변에 영향을 주면 안 되므로 로그만 남긴다
        logger.exception("질문 기록 저장 실패")


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

    CHAT_QUESTIONS.inc()
    repo = ChatLogRepository(request.app.state.db_pool)

    async def stream():
        started = time.monotonic()
        first_token: float | None = None
        answer = ""
        results = []
        status, error = "error", "예상하지 못한 서버 오류"
        try:
            results = await retriever.search(req.question, prev_question)
            yield sse("sources", [SourceDTO.from_domain(r).model_dump() for r in results])
            async for text in chat.stream_answer(req.question, history, results):
                if first_token is None:
                    first_token = time.monotonic() - started
                    CHAT_FIRST_TOKEN.observe(first_token)
                answer += text
                yield sse("delta", text)
            # 오류 없이 끝났어도, 문서에 정보가 없어 거절 문장으로 답했으면 따로 센다
            status, error = ("unanswered" if is_unanswered(answer) else "ok"), None
            sources = ", ".join(f"{r.chunk.title}({r.score:.2f})" for r in results)
            logger.info("답변 ip=%s %s %.1fs %d자 sources=[%s]", ip, status, time.monotonic() - started, len(answer), sources)
        except RuntimeError as e:
            status, error = "error", str(e)
            logger.warning("실패 ip=%s %.1fs error=%s", ip, time.monotonic() - started, e)
            yield sse("error", str(e))
        except (asyncio.CancelledError, GeneratorExit):
            # 답변이 끝나기 전에 방문자가 창을 닫거나 새 대화를 시작한 경우
            status, error = "cancelled", None
            raise
        finally:
            elapsed = time.monotonic() - started
            CHAT_ANSWERS.labels(status).inc()
            CHAT_DURATION.observe(elapsed)
            log = ChatLog(
                visitor=visitor_id(ip), question=req.question, history_turns=len(history),
                status=status, error=error, duration_ms=int(elapsed * 1000), answer=answer, answer_chars=len(answer),
                first_token_ms=int(first_token * 1000) if first_token is not None else None,
                sources=[{"title": r.chunk.title, "score": round(r.score, 2)} for r in results],
            )
            # 방문자가 창을 닫아 이 함수가 취소돼도 기록은 남도록 별도 태스크로 저장한다
            task = asyncio.create_task(save_log(repo, log))
            _background.add(task)
            task.add_done_callback(_background.discard)
        yield sse("done", {})

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
