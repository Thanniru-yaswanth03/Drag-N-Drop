# Kanban Studio - Backend Service

High-performance FastAPI backend service providing RESTful APIs, real-time WebSockets synchronization, AI assistant integration, and dual-engine persistence (PostgreSQL & SQLite) for the Kanban Studio project management platform.

## Features
- **FastAPI Framework**: Async REST endpoints with automated OpenAPI documentation.
- **Dual Database Persistence**: Automatic PostgreSQL connection pooling with SQLite fallback for local development.
- **Real-time WebSockets**: Instant multi-client synchronization for board updates, card movements, and column state changes.
- **Security & Authentication**: Production-grade JWT authentication, bcrypt password hashing, rate limiting, and CORS configuration.
- **AI Assistant**: Intelligent task decomposition, automatic priority estimation, and smart board recommendations.

## Running Locally

```bash
# Using uv
uv run uvicorn main:app --reload --port 8000

# Running tests
uv run pytest
```
