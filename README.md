# Multi Agent Townhall

This repository contains a learning project designed to build a clean multi-agent architecture.

The system simulates a **townhall discussion between AI agents** where each agent represents a character with their own personality and opinions.

Agents communicate through an event bus and maintain long-term memory using vector search.

The goal of this project is to create a reusable blueprint for multi-agent architectures.

## Core Technologies

- Redis Streams (event bus)
- Python services
- PostgreSQL with pgvector (vector memory)
- Docker / Docker Compose
- Config driven setup following the Twelve Factor App philosophy

## System Components

### Redis Stream

Acts as the message bus between agents.

All agents communicate through the `townhall` stream.

### Villager Agent Service

Responsible for:

- Listening to the Redis event stream
- Deciding whether to react to events
- Retrieving relevant memories
- Generating responses
- Publishing new events

### Memory Controller Service

Modelled after the **Mem0** framework (*Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory*), which provides scalable memory management through a structured update pipeline.

The memory lifecycle consists of two phases:

**Extract phase** — When an event is received, relevant information is extracted and compared against existing memories using vector similarity search.

**Update phase** — Based on the comparison, one of four operations is applied to the memory store:
- **ADD** — new information not present in existing memories
- **UPDATE** — existing memory is revised with new or corrected information
- **DELETE** — memory is no longer relevant and is removed
- **NOOP** — no change required; existing memory already captures the information

After the update phase, a **summary** is generated to provide a condensed, human-readable view of the agent's current memory state.

This approach ensures the memory store stays accurate and non-redundant over time, rather than growing unbounded.

### PostgreSQL + pgvector

Stores:

- memories
- embeddings
- metadata
- summaries

## Short Term Objective

Create a working local development system with:

- Redis
- PostgreSQL
- Villager Agent service
- Memory Controller service

All services run using Docker Compose.