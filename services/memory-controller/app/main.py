"""Memory Controller – main entry point."""

from __future__ import annotations

import logging
import signal
import time

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
from app.embedding_service import generate_embedding
from app.memory_service import process_event
from app.postgres_client import get_connection, store_memory
from shared.events.schema import Event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_running = True


def _shutdown(signum: int, _frame) -> None:
    global _running
    logger.info("Received signal %s – shutting down …", signum)
    _running = False


def _ensure_consumer_group(client: redis.Redis) -> None:
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


def _read_batch(client: redis.Redis) -> list[tuple[str, Event]]:
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
                results.append((mid, Event.from_stream_dict(data)))
            except Exception:
                logger.exception("Failed to parse event from message %s", mid)
    return results


def main() -> None:
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Starting Memory Controller on stream '%s'", STREAM_NAME)

    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    _ensure_consumer_group(redis_client)

    pg_conn = get_connection()

    def _store(agent_id: str, content: str, embedding: list[float], memory_type: str) -> str:
        return store_memory(pg_conn, agent_id, content, embedding, memory_type)

    while _running:
        try:
            events = _read_batch(redis_client)
            for message_id, event in events:
                try:
                    process_event(event, store_fn=_store, embed_fn=generate_embedding)
                except Exception:
                    logger.exception(
                        "Failed to process event %s – skipping", event.event_id
                    )
                finally:
                    redis_client.xack(STREAM_NAME, CONSUMER_GROUP, message_id)

        except KeyboardInterrupt:
            break
        except Exception:
            logger.exception("Error in event loop – retrying in 2 s")
            time.sleep(2)

    pg_conn.close()
    logger.info("Memory Controller shut down.")


if __name__ == "__main__":
    main()
