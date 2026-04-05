"""PostgreSQL client using psycopg2 + pgvector."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector

from app.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

logger = logging.getLogger(__name__)


def get_connection() -> psycopg2.extensions.connection:
    """Open and return a new psycopg2 connection with pgvector registered."""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    register_vector(conn)
    return conn


def store_memory(
    conn: psycopg2.extensions.connection,
    agent_id: str,
    content: str,
    embedding: list[float],
    memory_type: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Insert a new memory row and return the generated id."""
    memory_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO memories
                (id, agent_id, content, embedding, memory_type, metadata, created_at)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                memory_id,
                agent_id,
                content,
                embedding,
                memory_type,
                psycopg2.extras.Json(metadata) if metadata else None,
                created_at,
            ),
        )
    conn.commit()
    logger.debug("Stored memory %s for agent %s", memory_id, agent_id)
    return memory_id


def search_similar_memories(
    conn: psycopg2.extensions.connection,
    agent_id: str,
    embedding: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Return the top-k most similar non-summary memories for agent_id.

    Uses pgvector cosine distance (1 - cosine_similarity).
    Results are ordered by similarity descending.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                id::text,
                content,
                memory_type,
                1 - (embedding <=> %s::vector) AS similarity
            FROM memories
            WHERE agent_id = %s
              AND memory_type != 'summary'
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (embedding, agent_id, embedding, top_k),
        )
        rows = cur.fetchall()

    return [dict(r) for r in rows]


def update_memory(
    conn: psycopg2.extensions.connection,
    memory_id: str,
    content: str,
    embedding: list[float],
) -> None:
    """Update the content and embedding of an existing memory."""
    updated_at = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE memories
            SET content = %s, embedding = %s, updated_at = %s
            WHERE id = %s
            """,
            (content, embedding, updated_at, memory_id),
        )
    conn.commit()
    logger.debug("Updated memory %s", memory_id)


def delete_memory(
    conn: psycopg2.extensions.connection,
    memory_id: str,
) -> None:
    """Delete a memory row by id."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
    conn.commit()
    logger.debug("Deleted memory %s", memory_id)


def upsert_summary(
    conn: psycopg2.extensions.connection,
    agent_id: str,
    content: str,
    embedding: list[float],
) -> None:
    """Insert or update the single summary row for an agent."""
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        # Check for existing summary
        cur.execute(
            "SELECT id FROM memories WHERE agent_id = %s AND memory_type = 'summary' LIMIT 1",
            (agent_id,),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """
                UPDATE memories
                SET content = %s, embedding = %s, updated_at = %s
                WHERE id = %s
                """,
                (content, embedding, now, row[0]),
            )
        else:
            summary_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO memories
                    (id, agent_id, content, embedding, memory_type, created_at)
                VALUES
                    (%s, %s, %s, %s, 'summary', %s)
                """,
                (summary_id, agent_id, content, embedding, now),
            )
    conn.commit()
    logger.debug("Upserted summary for agent %s", agent_id)


def fetch_agent_memories(
    conn: psycopg2.extensions.connection,
    agent_id: str,
    exclude_summary: bool = True,
) -> list[dict[str, Any]]:
    """Return all memories for an agent, optionally excluding the summary row."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if exclude_summary:
            cur.execute(
                """
                SELECT id::text, content, memory_type, created_at
                FROM memories
                WHERE agent_id = %s AND memory_type != 'summary'
                ORDER BY created_at ASC
                """,
                (agent_id,),
            )
        else:
            cur.execute(
                """
                SELECT id::text, content, memory_type, created_at
                FROM memories
                WHERE agent_id = %s
                ORDER BY created_at ASC
                """,
                (agent_id,),
            )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def count_agent_memories(
    conn: psycopg2.extensions.connection,
    agent_id: str,
) -> int:
    """Return the number of non-summary memories for an agent."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM memories WHERE agent_id = %s AND memory_type != 'summary'",
            (agent_id,),
        )
        return cur.fetchone()[0]


def prune_memories(
    conn: psycopg2.extensions.connection,
    agent_id: str,
    keep_n: int,
) -> int:
    """Delete the oldest non-summary memories for agent_id, keeping only keep_n rows.

    Returns the number of rows deleted.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM memories
            WHERE agent_id = %s
              AND memory_type != 'summary'
              AND id NOT IN (
                  SELECT id FROM memories
                  WHERE agent_id = %s AND memory_type != 'summary'
                  ORDER BY COALESCE(updated_at, created_at) DESC
                  LIMIT %s
              )
            """,
            (agent_id, agent_id, keep_n),
        )
        deleted = cur.rowcount
    conn.commit()
    if deleted:
        logger.info("Pruned %d old memories for agent %s", deleted, agent_id)
    return deleted
