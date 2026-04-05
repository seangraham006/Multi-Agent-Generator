"""Configuration loaded from environment variables."""

import os

from shared.config_loader import validate_streams

validate_streams()

# Redis
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

STREAM_NAME: str = os.getenv("STREAM_NAME", "townhall")
CONSUMER_GROUP: str = os.getenv("CONSUMER_GROUP", "memory-controller-group")
CONSUMER_NAME: str = os.getenv("CONSUMER_NAME", "memory-controller-1")

# How long to block waiting for new messages (ms)
BLOCK_MS: int = int(os.getenv("BLOCK_MS", "5000"))

# Number of messages to read per batch
BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))

# PostgreSQL
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "villager_memory")
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")

# Embedding model (sentence-transformers model name)
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "384"))

# Mistral LLM
MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

# Memory pipeline
# How many similar memories to retrieve for comparison
SIMILARITY_TOP_K: int = int(os.getenv("SIMILARITY_TOP_K", "5"))
# Maximum non-summary memories to retain per agent before pruning oldest
MAX_MEMORIES_PER_AGENT: int = int(os.getenv("MAX_MEMORIES_PER_AGENT", "100"))
