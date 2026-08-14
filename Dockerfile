# Stage 1: Build Next.js static export
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY pm/frontend/package*.json ./
RUN npm ci
COPY pm/frontend/ ./
RUN npm run build

# Stage 2: Python FastAPI backend + bundled static frontend
FROM python:3.13-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

COPY pm/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pm/backend/ .
COPY --from=frontend-builder /app/frontend/out ./static

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
