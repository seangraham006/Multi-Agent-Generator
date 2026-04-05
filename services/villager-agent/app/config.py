"""Configuration loaded from environment variables."""

import os

from shared.config_loader import validate_streams

validate_streams()

REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

STREAM_NAME: str = os.getenv("STREAM_NAME", "townhall")

AGENT_ID: str = os.getenv("AGENT_ID", "villager")
CONSUMER_GROUP: str = os.getenv("CONSUMER_GROUP", "villager-group")
CONSUMER_NAME: str = os.getenv("CONSUMER_NAME", "villager-1")

# How long to block waiting for new messages (ms)
BLOCK_MS: int = int(os.getenv("BLOCK_MS", "5000"))

# Number of messages to read per batch
BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
