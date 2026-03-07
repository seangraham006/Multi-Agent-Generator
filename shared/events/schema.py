"""Event schema for inter-agent communication via Redis Streams."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    SPEECH = "speech"
    QUESTION = "question"
    VOTE = "vote"
    SYSTEM = "system"


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    agent_id: str
    content: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_stream_dict(self) -> dict[str, str]:
        """Serialize to a flat dict suitable for Redis Stream XADD."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_stream_dict(cls, data: dict[bytes | str, bytes | str]) -> Event:
        """Deserialize a Redis Stream entry back into an Event."""
        decoded = {
            (k.decode() if isinstance(k, bytes) else k): (
                v.decode() if isinstance(v, bytes) else v
            )
            for k, v in data.items()
        }
        return cls(**decoded)
