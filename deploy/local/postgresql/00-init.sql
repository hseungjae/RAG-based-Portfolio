-- 컨테이너 최초 실행 시 한 번만 적용된다.
-- 벡터 차원(1024)은 settings.embedding_dimension 과 같아야 한다.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS profile_chunk (
    chunk_id   INTEGER PRIMARY KEY,
    source     TEXT NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    embedding  vector(1024) NOT NULL
);

CREATE INDEX IF NOT EXISTS profile_chunk_embedding_idx
    ON profile_chunk USING hnsw (embedding vector_cosine_ops);
