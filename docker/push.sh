#!/bin/bash
# Push Docker image(s) to DockerHub.
# Usage (from roundtable/ root):
#   bash docker/push.sh            # push both
#   bash docker/push.sh backend    # push backend only
#   bash docker/push.sh frontend   # push frontend (nginx) only
# Or use: make push
# For full build + push: make release

set -e

cd "$(dirname "$0")/.."

REGISTRY="simjay"
TAG="${TAG:-latest}"
TARGET="${1:-both}"

push_backend() {
  echo "→ Pushing backend image..."
  docker push ${REGISTRY}/roundtable-backend:${TAG}
  echo "✓ Pushed: ${REGISTRY}/roundtable-backend:${TAG}"
}

push_frontend() {
  echo "→ Pushing nginx+frontend image..."
  docker push ${REGISTRY}/roundtable-nginx:${TAG}
  echo "✓ Pushed: ${REGISTRY}/roundtable-nginx:${TAG}"
}

echo "Pushing roundtable images to DockerHub (tag: ${TAG})"
echo ""

case "$TARGET" in
  backend)  push_backend ;;
  frontend) push_frontend ;;
  both)     push_backend; echo ""; push_frontend ;;
  *)
    echo "Unknown target: $TARGET. Use: backend | frontend | both"
    exit 1
    ;;
esac

echo ""
echo "Deploy on Hostinger using:"
echo "  https://raw.githubusercontent.com/simjay/roundtable/main/docker/docker-compose.yml"
echo ""
echo "Required environment variables on VPS:"
echo "  SUPABASE_URL, SUPABASE_SECRET_KEY, SUPABASE_ANON_KEY, APP_URL, ADMIN_KEY"
