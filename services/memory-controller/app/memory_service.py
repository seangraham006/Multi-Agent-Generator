"""Evaluate events and persist relevant ones as memories."""

from __future__ import annotations

import logging

from shared.events.schema import Event, EventType

logger = logging.getLogger(__name__)

# Map event types to memory types.
# system events are not persisted.
_EVENT_TO_MEMORY_TYPE: dict[EventType, str] = {
    EventType.SPEECH: "episodic",
    EventType.QUESTION: "episodic",
    EventType.VOTE: "semantic",
}


def should_store(event: Event) -> bool:
    """Return True if this event is worth storing as a memory.

    Current policy:
    - Store all speech, question, and vote events.
    - Ignore system events (infrastructure noise, not social content).
    - Ignore events with empty content.
    """
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
    store_fn,
    embed_fn,
) -> bool:
    """Evaluate an event, generate an embedding, and persist if appropriate.

    Parameters
    ----------
    event:    The incoming Event from the stream.
    store_fn: Callable(agent_id, content, embedding, memory_type) → memory_id.
    embed_fn: Callable(text) → list[float].

    Returns True if the event was stored, False otherwise.
    """
    if not should_store(event):
        logger.debug(
            "Skipping event %s (type=%s)", event.event_id, event.event_type
        )
        return False

    memory_type = resolve_memory_type(event)
    embedding = embed_fn(event.content)

    memory_id = store_fn(
        agent_id=event.agent_id,
        content=event.content,
        embedding=embedding,
        memory_type=memory_type,
    )
    logger.info(
        "Stored memory %s | agent=%s type=%s",
        memory_id,
        event.agent_id,
        memory_type,
    )
    return True
