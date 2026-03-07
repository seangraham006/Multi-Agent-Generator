# Database Design

The system uses PostgreSQL with pgvector for vector similarity search.

## Memory Table

memories

Columns:

id
primary key

agent_id
agent that owns this memory

content
text representation of the memory

embedding
vector embedding

memory_type

Possible values:

episodic
semantic
summary

created_at
timestamp

## Example Query

Retrieve most relevant memories:

SELECT content
FROM memories
ORDER BY embedding <-> query_embedding
LIMIT 5;

## Extensions

pgvector must be enabled:

CREATE EXTENSION vector;