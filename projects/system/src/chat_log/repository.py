import json

import asyncpg

from src.domain import ChatLog

# 기존 DB에도 바로 생기도록 서버가 시작할 때 만든다 (init SQL 은 DB를 처음 만들 때만 실행되므로)
SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_log (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    visitor         TEXT NOT NULL,
    question        TEXT NOT NULL,
    history_turns   INTEGER NOT NULL,
    status          TEXT NOT NULL,
    error           TEXT,
    answer_chars    INTEGER NOT NULL,
    first_token_ms  INTEGER,
    duration_ms     INTEGER NOT NULL,
    sources         JSONB
);
CREATE INDEX IF NOT EXISTS chat_log_created_at_idx ON chat_log (created_at);
-- 답변 내용은 나중에 추가한 컬럼이라, 이미 만들어진 테이블에도 붙도록 따로 추가한다
ALTER TABLE chat_log ADD COLUMN IF NOT EXISTS answer TEXT;
"""


class ChatLogRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def ensure_schema(self) -> None:
        await self.pool.execute(SCHEMA)

    async def insert(self, log: ChatLog) -> None:
        await self.pool.execute(
            "INSERT INTO chat_log (visitor, question, history_turns, status, error,"
            " answer, answer_chars, first_token_ms, duration_ms, sources)"
            " VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)",
            log.visitor, log.question, log.history_turns, log.status, log.error,
            log.answer, log.answer_chars, log.first_token_ms, log.duration_ms,
            json.dumps(log.sources, ensure_ascii=False) if log.sources is not None else None,
        )
