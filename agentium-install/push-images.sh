#!/usr/bin/env bash
# Run this once to push Agentium images to Docker Hub.
# Usage: bash push-images.sh <dockerhub-username>
# Example: bash push-images.sh agentiumhq

set -e

HUB_USER="${1:-agentiumhq}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔐 Logging into Docker Hub as: $HUB_USER"
docker login

echo ""
echo "🏗  Building images from source..."
cd "$ROOT"
docker compose build backend customer-dashboard-v3

echo ""
echo "🏷  Tagging images..."
docker tag agent-runtime-layer-backend:latest        "$HUB_USER/backend:latest"
docker tag agent-runtime-layer-customer-dashboard-v3:latest "$HUB_USER/dashboard:latest"

echo ""
echo "📤 Pushing to Docker Hub..."
docker push "$HUB_USER/backend:latest"
docker push "$HUB_USER/dashboard:latest"

echo ""
echo "✅ Done! Images live at:"
echo "   https://hub.docker.com/r/$HUB_USER/backend"
echo "   https://hub.docker.com/r/$HUB_USER/dashboard"
echo ""
echo "📝 Update agentium-install/docker-compose.yml image names to:"
echo "   image: $HUB_USER/backend:latest"
echo "   image: $HUB_USER/dashboard:latest"
