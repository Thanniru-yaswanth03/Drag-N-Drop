# Backend Architecture & Implementation

## Overview

The `backend` directory contains the Python FastAPI web service powering the Project Management MVP with SQLite persistence.

## Technology Stack

- Framework: FastAPI 0.110+
- Server: Uvicorn
- Database: SQLite (`pm.db`)
- Package Manager: `uv` (inside Docker) / `pip`
- Validation: Pydantic v2 & `jsonschema`
- Testing: pytest + HTTPX / FastAPI TestClient

## File Structure

- `main.py`: FastAPI application entrypoint with RESTful route definitions.
- `database.py`: SQLite connection manager, table schema creation, default board seeding, and CRUD database functions.
- `test_main.py`: Unit test suite verifying Auth and Health API endpoints.
- `test_database.py`: Integration test suite verifying SQLite database operations and Kanban board CRUD routes.
- `test_schema.py`: JSON Schema validation test suite verifying board payload compliance with `docs/schema.json`.
- `pyproject.toml`: Python package definitions and pytest configuration.
- `requirements.txt`: Pip requirements file for container builds and local execution.

## Endpoints

- `GET /api/health`: Health check route returning `{"status": "ok"}`.
- `POST /api/auth/login`: Authenticates credentials (`user` / `password`).
- `POST /api/auth/logout`: Clears user session.
- `GET /api/board`: Returns current Kanban board JSON structure for user.
- `PUT /api/board`: Saves updated Kanban board JSON structure.
- `POST /api/cards`: Adds new card to specified column.
- `DELETE /api/cards/{card_id}`: Deletes a card by ID.
- `GET /`: Root endpoint serving Next.js static HTML build.

## Testing

Run complete backend test suite locally:
```bash
python -m pytest
```