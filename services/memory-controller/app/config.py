"""Configuration loaded from environment variables."""

import os

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
