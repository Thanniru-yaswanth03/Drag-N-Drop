# Multi-Stage Production Dockerfile for Kanban Studio

# Stage 1: Build Next.js Static Export
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Application Runtime
FROM python:3.13-slim AS runner
WORKDIR /app/backend

# Prevent Python from writing .pyc files & enable unbuffered stdout
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    PORT=8000

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

# Install Python requirements
COPY backend/pyproject.toml backend/requirements.txt* ./
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic python-dotenv

# Copy backend code
COPY backend/ ./

# Copy static frontend export build into backend static directory
COPY --from=frontend-builder /app/frontend/out ./static

# Ensure persistent mount directory exists
RUN mkdir -p /data

ENV DATABASE_PATH=/data/pm.db

# Expose production application port
EXPOSE 8000


# Healthcheck definition
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start production uvicorn server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
