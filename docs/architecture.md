# System Architecture

This project implements a minimal multi-agent architecture.

Agents communicate through events and maintain memory through a separate memory system.

The design intentionally favors clarity over scalability for the first iteration.

Future versions will consolidate services.

## Event Driven Architecture

Agents do not communicate directly.

Instead they emit and react to events via Redis Streams.

Architecture:

Agent → Event Bus → Agent

## Components

### Redis Streams

Acts as the event bus.

Stream name:

townhall

All agents subscribe to this stream.

### Agent Services

Each agent runs in its own Python service.

Responsibilities:

- listen for events
- determine if the agent should respond
- retrieve memories
- generate responses
- publish events

### Memory Controller

Each agent has a memory controller responsible for deciding if an event should become long term memory.

Responsibilities:

- filter events
- generate embeddings
- store memories
- update summaries

### Database

Each memory controller writes to PostgreSQL with pgvector enabled.

Memories contain:

- content
- embedding
- metadata
- timestamps

## Development Principles

The project follows principles from the Twelve Factor App:

- config driven infrastructure
- stateless services
- environment variables
- clear separation between services