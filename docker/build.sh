#!/bin/bash
# Build Docker image(s) for Roundtable.
# Usage (from roundtable/ root):
#   bash docker/build.sh           # build both
#   bash docker/build.sh backend   # build backend only
#   bash docker/build.sh frontend  # build frontend (nginx) only
# Or use: make build | make build-backend | make build-frontend

set -e

# Always resolve paths relative to roundtable/ root
cd "$(dirname "$0")/.."

REGISTRY="simjay"
TAG="${TAG:-latest}"
TARGET="${1:-both}"

# Set DOCKER_PLATFORM=linux/amd64 on Mac to cross-compile for Linux.
# Leave unset on Linux to build natively.
if [ -n "${DOCKER_PLATFORM}" ]; then
  PLATFORM_FLAG="--platform ${DOCKER_PLATFORM}"
else
  PLATFORM_FLAG=""
fi

build_backend() {
  echo "→ Building backend image..."
  docker build \
    ${PLATFORM_FLAG} \
    -f backend/Dockerfile \
    -t ${REGISTRY}/roundtable-backend:${TAG} \
    .
  echo "✓ Backend built: ${REGISTRY}/roundtable-backend:${TAG}"
}

build_frontend() {
  echo "→ Building nginx+frontend image..."
  docker build \
    ${PLATFORM_FLAG} \
    -t ${REGISTRY}/roundtable-nginx:${TAG} \
    ./frontend
  echo "✓ Frontend built: ${REGISTRY}/roundtable-nginx:${TAG}"
}

echo "Building roundtable images (tag: ${TAG}, platform: ${DOCKER_PLATFORM:-native})"
echo ""

case "$TARGET" in
  backend)  build_backend ;;
  frontend) build_frontend ;;
  both)     build_backend; echo ""; build_frontend ;;
  *)
    echo "Unknown target: $TARGET. Use: backend | frontend | both"
    exit 1
    ;;
esac

echo ""
echo "Done. Run 'make push' to push to DockerHub."
