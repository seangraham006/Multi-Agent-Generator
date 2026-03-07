"""Agent decision-making logic."""

from __future__ import annotations

import logging
from typing import Optional

from app.config import AGENT_ID
from shared.events.schema import Event, EventType

logger = logging.getLogger(__name__)


def should_respond(event: Event) -> bool:
    """Decide whether the agent should respond to an incoming event.

    Current heuristic:
    - Ignore events produced by this agent (no echo loops).
    - Respond to speech and question events from other agents.
    - Ignore system events.
    """
    if event.agent_id == AGENT_ID:
        return False

    if event.event_type in (EventType.SPEECH, EventType.QUESTION):
        return True

    return False


def generate_response(event: Event) -> Optional[Event]:
    """Produce a response event given an incoming event.

    Returns None if no response is warranted.
    """
    if not should_respond(event):
        return None

    # --- placeholder response logic ---
    # In a full implementation this would call an LLM, retrieve memories, etc.
    if event.event_type == EventType.QUESTION:
        content = f"[{AGENT_ID}] I think that's a great question, {event.agent_id}."
        response_type = EventType.SPEECH
    else:
        content = f"[{AGENT_ID}] Interesting point, {event.agent_id}. I have thoughts on that."
        response_type = EventType.SPEECH

    response = Event(
        event_type=response_type,
        agent_id=AGENT_ID,
        content=content,
    )
    logger.info("Generated response: %s", response.content)
    return response
