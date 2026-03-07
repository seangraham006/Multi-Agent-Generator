"""Villager Agent – main entry point."""

from __future__ import annotations

import logging
import signal
import sys
import time

from app.agent_logic import generate_response
from app.config import AGENT_ID, STREAM_NAME
from app.redis_client import (
    acknowledge,
    ensure_consumer_group,
    get_redis_connection,
    publish_event,
    read_events,
)

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


def main() -> None:
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Starting Villager Agent '%s' on stream '%s'", AGENT_ID, STREAM_NAME)

    client = get_redis_connection()
    ensure_consumer_group(client)

    while _running:
        try:
            events = read_events(client)
            for message_id, event in events:
                logger.info(
                    "Received event %s from %s: %s",
                    event.event_id,
                    event.agent_id,
                    event.content[:80],
                )

                response = generate_response(event)
                if response is not None:
                    publish_event(client, response)

                acknowledge(client, message_id)

        except KeyboardInterrupt:
            break
        except Exception:
            logger.exception("Error in event loop – retrying in 2 s")
            time.sleep(2)

    logger.info("Villager Agent shut down.")


if __name__ == "__main__":
    main()
