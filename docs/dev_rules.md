# Development Rules

Language: Python 3.11

Libraries:

redis
pydantic
psycopg2
pgvector

Architecture:

Each service should contain:

app/main.py
app/config.py
app/service logic

Services should be stateless.

Configuration should be loaded from environment variables or config files.

Redis Streams should be used for message passing.

All events must follow the Event schema defined in shared/events/schema.py.