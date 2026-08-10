# Platform Operations & Control Scripts

## Overview

The `scripts` directory contains cross-platform operational scripts to build, start, and stop the `pm-app` Docker container.

## Available Scripts

### Linux / Mac (Bash)
- `./scripts/start.sh`: Builds the Docker image `pm-app` and starts the container on port 8000.
- `./scripts/stop.sh`: Stops and removes the running `pm-app` container.

### Windows (CMD)
- `scripts\start.bat`: Builds and starts the container on port 8000.
- `scripts\stop.bat`: Stops and removes the container.

### Windows (PowerShell)
- `.\scripts\start.ps1`: Builds and starts the container on port 8000.
- `.\scripts\stop.ps1`: Stops and removes the container.

## Ports and Services

- Web App & API: `http://localhost:8000`
- Health Check: `http://localhost:8000/api/health`