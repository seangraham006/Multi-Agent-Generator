# Event Schema

All communication between agents must follow this schema.

Events are published to the Redis Stream `townhall`.

## Event Structure

event_id
Unique identifier for the event.

event_type
Type of event.

Examples:

speech
question
vote
system

agent_id
The agent that produced the event.

content
The natural language content of the event.

timestamp
UTC timestamp.

## Example Event

{
  "event_id": "uuid",
  "event_type": "speech",
  "agent_id": "farmer",
  "content": "I believe grain taxes should be lowered.",
  "timestamp": "2026-03-07T12:00:00Z"
}

## Event Processing

Agents must:

1. Read events from the Redis stream
2. Determine if the event is relevant
3. Retrieve relevant memories
4. Generate a response if appropriate