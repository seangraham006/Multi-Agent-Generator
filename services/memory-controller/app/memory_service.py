"""Mem0-style memory pipeline: Extract → Classify → Update → Summarise."""

from __future__ import annotations

import json
import logging

import psycopg2.extensions

from shared.events.schema import Event, EventType
from app.config import MAX_MEMORIES_PER_AGENT, SIMILARITY_TOP_K
from app import postgres_client as db
from app.llm_service import classify_memory_action, generate_summary

logger = logging.getLogger(__name__)

# Map event types to memory types; SYSTEM events are never stored.
_EVENT_TO_MEMORY_TYPE: dict[EventType, str] = {
    EventType.SPEECH: "episodic",
    EventType.QUESTION: "episodic",
    EventType.VOTE: "semantic",
}


def should_store(event: Event) -> bool:
    """Return True if this event is worth processing through the memory pipeline."""
    if event.event_type == EventType.SYSTEM:
        return False
    if not event.content.strip():
        return False
    return True


def resolve_memory_type(event: Event) -> str:
    """Map an event type to a memory_type string for storage."""
    return _EVENT_TO_MEMORY_TYPE.get(event.event_type, "episodic")


def process_event(
    event: Event,
    conn: psycopg2.extensions.connection,
    embed_fn,
) -> str:
    """Run the full Mem0-style pipeline for a single event.

    Pipeline stages:
      1. Filter      – skip events that should not be stored.
      2. Embed       – generate a vector embedding of the event content.
      3. Extract     – retrieve the top-k most similar existing memories.
      4. Classify    – ask the LLM for ADD / UPDATE / DELETE / NOOP decision.
      5. Update      – execute the decided action against the database.
      6. Summarise   – regenerate the agent's summary after any write.
      7. Prune       – remove oldest memories if over the per-agent cap.

    Parameters
    ----------
    event:    The incoming Event from the stream.
    conn:     An open psycopg2 connection (with pgvector registered).
    embed_fn: Callable(text: str) -> list[float].

    Returns
    -------
    The action taken: "SKIP", "ADD", "UPDATE", "DELETE", or "NOOP".
    """
    # ── 1. Filter ────────────────────────────────────────────────────────────
    if not should_store(event):
        logger.debug("Skipping event %s (type=%s)", event.event_id, event.event_type)
        return "SKIP"

    memory_type = resolve_memory_type(event)

    # ── 2. Embed ─────────────────────────────────────────────────────────────
    embedding = embed_fn(event.content)

    # ── 3. Extract – find similar existing memories ──────────────────────────
    similar = db.search_similar_memories(
        conn,
        agent_id=event.agent_id,
        embedding=embedding,
        top_k=SIMILARITY_TOP_K,
    )

    # ── 4. Classify – LLM decides ADD / UPDATE / DELETE / NOOP ───────────────
    decision = classify_memory_action(event.content, similar)
    action: str = decision["action"]
    target_id: str | None = decision.get("target_id")

    # ── 5. Update – execute the action ───────────────────────────────────────
    memory_id: str | None = None

    if action == "ADD":
        memory_id = db.store_memory(
            conn,
            agent_id=event.agent_id,
            content=event.content,
            embedding=embedding,
            memory_type=memory_type,
            metadata={"event_id": event.event_id, "event_type": event.event_type},
        )

    elif action == "UPDATE" and target_id:
        db.update_memory(conn, memory_id=target_id, content=event.content, embedding=embedding)
        memory_id = target_id

    elif action == "DELETE" and target_id:
        db.delete_memory(conn, memory_id=target_id)
        # After deleting the contradicted memory, store the new content.
        memory_id = db.store_memory(
            conn,
            agent_id=event.agent_id,
            content=event.content,
            embedding=embedding,
            memory_type=memory_type,
            metadata={"event_id": event.event_id, "event_type": event.event_type},
        )

    elif action == "NOOP":
        logger.info(
            json.dumps({
                "event": "memory_pipeline",
                "event_id": event.event_id,
                "agent_id": event.agent_id,
                "action": "NOOP",
                "target_id": target_id,
                "similarity": similar[0]["similarity"] if similar else None,
                "memory_type": memory_type,
            })
        )
        return "NOOP"

    else:
        # Fallback: malformed LLM response or UPDATE/DELETE without a target_id
        logger.warning(
            "Unresolvable action '%s' with target_id=%s for event %s – falling back to ADD",
            action,
            target_id,
            event.event_id,
        )
        action = "ADD"
        memory_id = db.store_memory(
            conn,
            agent_id=event.agent_id,
            content=event.content,
            embedding=embedding,
            memory_type=memory_type,
            metadata={"event_id": event.event_id, "event_type": event.event_type},
        )

    # ── Structured log ───────────────────────────────────────────────────────
    logger.info(
        json.dumps({
            "event": "memory_pipeline",
            "event_id": event.event_id,
            "agent_id": event.agent_id,
            "action": action,
            "memory_id": memory_id,
            "target_id": target_id,
            "similarity": similar[0]["similarity"] if similar else None,
            "memory_type": memory_type,
        })
    )

    # ── 6. Summarise – regenerate agent summary after any write ──────────────
    _update_summary(conn, event.agent_id, embed_fn)

    # ── 7. Prune – enforce per-agent memory cap ───────────────────────────────
    count = db.count_agent_memories(conn, event.agent_id)
    if count > MAX_MEMORIES_PER_AGENT:
        db.prune_memories(conn, event.agent_id, keep_n=MAX_MEMORIES_PER_AGENT)

    return action


def _update_summary(
    conn: psycopg2.extensions.connection,
    agent_id: str,
    embed_fn,
) -> None:
    """Regenerate and upsert the LLM summary for an agent."""
    memories = db.fetch_agent_memories(conn, agent_id, exclude_summary=True)
    if not memories:
        return

    summary_text = generate_summary(agent_id, memories)
    if not summary_text:
        return

    summary_embedding = embed_fn(summary_text)
    db.upsert_summary(conn, agent_id, summary_text, summary_embedding)
    logger.debug("Updated summary for agent %s (%d memories)", agent_id, len(memories))
