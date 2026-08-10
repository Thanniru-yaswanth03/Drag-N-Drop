# Stage 1: Build Next.js frontend static export
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python FastAPI runtime
FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.12-slim

WORKDIR /app

# Copy uv binary
COPY --from=uv_bin /uv /uvx /bin/

# Copy backend files
COPY backend/ /app/backend/

# Copy static frontend export into backend/static
COPY --from=frontend-builder /app/frontend/out /app/backend/static

WORKDIR /app/backend

# Install python dependencies
RUN uv pip install --system -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
