-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Memories table for all agents
CREATE TABLE IF NOT EXISTS memories (
    id          UUID PRIMARY KEY,
    agent_id    TEXT        NOT NULL,
    content     TEXT        NOT NULL,
    embedding   vector(384) NOT NULL,
    memory_type TEXT        NOT NULL CHECK (memory_type IN ('episodic', 'semantic', 'summary')),
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ
);

-- Index for fast cosine-similarity lookups (hnsw is better for small-to-medium datasets)
CREATE INDEX IF NOT EXISTS memories_embedding_idx
    ON memories
    USING hnsw (embedding vector_cosine_ops);

-- Index for per-agent queries
CREATE INDEX IF NOT EXISTS memories_agent_idx
    ON memories (agent_id);
