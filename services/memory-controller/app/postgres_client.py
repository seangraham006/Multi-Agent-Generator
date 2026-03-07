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
) -> str:
    """Insert a memory row and return the generated id."""
    memory_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO memories
                (id, agent_id, content, embedding, memory_type, created_at)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (memory_id, agent_id, content, embedding, memory_type, created_at),
        )
    conn.commit()
    logger.debug("Stored memory %s for agent %s", memory_id, agent_id)
    return memory_id
