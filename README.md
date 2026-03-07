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

Responsible for:

- Evaluating events
- Deciding if events should become long term memory
- Storing memories
- Generating summaries

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