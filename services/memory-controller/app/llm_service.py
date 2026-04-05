"""LLM-powered memory classification and summarisation via Mistral API."""

from __future__ import annotations

import json
import logging

from mistralai import Mistral

from app.config import MISTRAL_API_KEY, MISTRAL_MODEL

logger = logging.getLogger(__name__)

_client: Mistral | None = None


def _get_client() -> Mistral:
    global _client
    if _client is None:
        if not MISTRAL_API_KEY:
            raise RuntimeError("MISTRAL_API_KEY is not set")
        _client = Mistral(api_key=MISTRAL_API_KEY)
    return _client


def classify_memory_action(new_content: str, similar_memories: list[dict]) -> dict:
    """Ask Mistral to decide ADD / UPDATE / DELETE / NOOP for a new memory.

    Parameters
    ----------
    new_content:      The content of the incoming event.
    similar_memories: List of dicts with keys: id, content, similarity, memory_type.

    Returns
    -------
    dict with keys:
      action    – one of "ADD", "UPDATE", "DELETE", "NOOP"
      target_id – UUID string of the memory to UPDATE/DELETE, or None
    """
    if not similar_memories:
        return {"action": "ADD", "target_id": None}

    existing_text = "\n".join(
        f"[{m['id']}] (similarity={m['similarity']:.3f}) {m['content']}"
        for m in similar_memories
    )

    prompt = (
        "You are a memory manager for an AI agent. "
        "Given a set of existing memories and new incoming content, decide what to do.\n\n"
        "EXISTING MEMORIES (format: [id] (similarity) content):\n"
        f"{existing_text}\n\n"
        f"NEW CONTENT:\n{new_content}\n\n"
        "Choose exactly one action:\n"
        "- ADD    : The new content is distinct and adds new information.\n"
        "- UPDATE : The new content revises or extends a specific existing memory. "
        "           Set target_id to that memory's id.\n"
        "- NOOP   : The existing memories already fully capture this information.\n"
        "- DELETE : The new content explicitly contradicts an existing memory. "
        "           Set target_id to the memory to remove (the new content will be ADDed separately).\n\n"
        'Respond with ONLY a JSON object, no markdown, no explanation:\n'
        '{"action": "ADD"|"UPDATE"|"NOOP"|"DELETE", "target_id": "<id or null>"}'
    )

    client = _get_client()
    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON: %s – defaulting to ADD", raw)
        return {"action": "ADD", "target_id": None}

    if result.get("action") not in ("ADD", "UPDATE", "NOOP", "DELETE"):
        logger.warning("LLM returned unexpected action '%s' – defaulting to ADD", result.get("action"))
        return {"action": "ADD", "target_id": None}

    # Normalise null-like target_id
    if result.get("target_id") in (None, "null", ""):
        result["target_id"] = None

    logger.debug("LLM classification: %s", result)
    return result


def generate_summary(agent_id: str, memories: list[dict]) -> str:
    """Ask Mistral to produce a concise summary of an agent's current memory state.

    Parameters
    ----------
    agent_id: Identifier for the agent (used for context in the prompt).
    memories: List of dicts with keys: content, memory_type.

    Returns
    -------
    A plain-text summary string.
    """
    if not memories:
        return ""

    memory_text = "\n".join(
        f"- [{m['memory_type']}] {m['content']}"
        for m in memories
    )

    prompt = (
        f"You are summarising the memory state of an AI agent named '{agent_id}'.\n\n"
        "CURRENT MEMORIES:\n"
        f"{memory_text}\n\n"
        "Write a concise summary (3-5 sentences) of what this agent currently knows, "
        "believes, and has experienced. Deduplicate and merge related points. "
        "Write in third-person about the agent."
    )

    client = _get_client()
    response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
