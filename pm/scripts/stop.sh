#!/usr/bin/env bash
set -e

echo "Stopping container pm-app..."
docker stop pm-app 2>/dev/null || true

echo "Removing container pm-app..."
docker rm pm-app 2>/dev/null || true

echo "Container stopped and removed successfully."
