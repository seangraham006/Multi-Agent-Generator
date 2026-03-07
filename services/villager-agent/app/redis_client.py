"""Redis client and stream helpers."""

from __future__ import annotations

import logging

import redis

from app.config import (
    BATCH_SIZE,
    BLOCK_MS,
    CONSUMER_GROUP,
    CONSUMER_NAME,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PORT,
    STREAM_NAME,
)
from shared.events.schema import Event

logger = logging.getLogger(__name__)


def get_redis_connection() -> redis.Redis:
    """Create and return a Redis connection."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def ensure_consumer_group(client: redis.Redis) -> None:
    """Create the consumer group if it does not already exist."""
    try:
        client.xgroup_create(
            name=STREAM_NAME,
            groupname=CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
        logger.info(
            "Created consumer group '%s' on stream '%s'",
            CONSUMER_GROUP,
            STREAM_NAME,
        )
    except redis.exceptions.ResponseError as exc:
        if "BUSYGROUP" in str(exc):
            logger.debug("Consumer group '%s' already exists", CONSUMER_GROUP)
        else:
            raise


def read_events(client: redis.Redis) -> list[tuple[str, Event]]:
    """Read a batch of events from the stream.

    Returns a list of (stream_message_id, Event) tuples.
    """
    results: list[tuple[str, Event]] = []
    response = client.xreadgroup(
        groupname=CONSUMER_GROUP,
        consumername=CONSUMER_NAME,
        streams={STREAM_NAME: ">"},
        count=BATCH_SIZE,
        block=BLOCK_MS,
    )
    if not response:
        return results

    for _stream_key, messages in response:
        for message_id, data in messages:
            mid = message_id.decode() if isinstance(message_id, bytes) else message_id
            try:
                event = Event.from_stream_dict(data)
                results.append((mid, event))
            except Exception:
                logger.exception("Failed to parse event from message %s", mid)
    return results


def acknowledge(client: redis.Redis, message_id: str) -> None:
    """Acknowledge a processed message."""
    client.xack(STREAM_NAME, CONSUMER_GROUP, message_id)


def publish_event(client: redis.Redis, event: Event) -> str:
    """Publish an event to the stream and return the message id."""
    mid = client.xadd(STREAM_NAME, event.to_stream_dict())
    return mid.decode() if isinstance(mid, bytes) else mid
