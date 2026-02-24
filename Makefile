# Roundtable — Makefile
# Run from the roundtable/ root directory.

REGISTRY     = simjay
TAG          = latest
PYTHON       = /opt/homebrew/bin/python3.12

# Full paths into the venv — avoids needing `source` (which is a shell built-in)
VENV         = backend/.venv
VENV_BIN     = $(VENV)/bin
VENV_PIP     = $(VENV_BIN)/pip
VENV_UVICORN = $(VENV_BIN)/uvicorn
VENV_PYTEST  = $(VENV_BIN)/pytest

# Docker platform flag:
#   Set DOCKER_PLATFORM=linux/amd64 in your shell to cross-compile (e.g. on Mac).
#   Leave unset on Linux to build natively.
ifdef DOCKER_PLATFORM
  PLATFORM_FLAG = --platform $(DOCKER_PLATFORM)
else
  PLATFORM_FLAG =
endif

.PHONY: install install-backend install-frontend \
        dev backend frontend \
        build build-backend build-frontend \
        push push-backend push-frontend \
        release \
        docker-dev \
        test \
        clean help

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Roundtable — available targets:"
	@echo ""
	@echo "  make install           Install backend + frontend dependencies"
	@echo "  make install-backend   Create .venv and pip install -e .[dev]"
	@echo "  make install-frontend  npm install in frontend/"
	@echo ""
	@echo "  make dev               Start backend + frontend in parallel"
	@echo "  make backend           Start backend dev server only  (:8000)"
	@echo "  make frontend          Start frontend dev server only (:5173)"
	@echo ""
	@echo "  make build             Build both Docker images"
	@echo "  make build-backend     Build backend image only"
	@echo "  make build-frontend    Build nginx+frontend image only"
	@echo "  make push              Push both images to DockerHub"
	@echo "  make push-backend      Push backend image only"
	@echo "  make push-frontend     Push frontend image only"
	@echo "  make release           Build + push both images (full deploy prep)"
	@echo "  make docker-dev        Run full stack via docker/docker-compose.dev.yml"
	@echo ""
	@echo "  make test              Run all backend unit tests"
	@echo "  make clean             Remove build artifacts"
	@echo ""
	@echo "  DOCKER_PLATFORM=linux/amd64 make build   (cross-compile for Linux)"
	@echo ""

# ── Install ───────────────────────────────────────────────────────────────────

install: install-backend install-frontend

install-backend:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip --quiet
	$(VENV_PIP) install -e "backend/.[dev]" --quiet
	@echo "Backend dependencies installed."

install-frontend:
	cd frontend && npm install
	@echo "Frontend dependencies installed."

# ── Local dev ─────────────────────────────────────────────────────────────────

# Run both services in parallel. Each prints to its own output.
# Ctrl-C stops both.
dev:
	$(MAKE) -j2 backend frontend

backend:
	cd backend && $(abspath $(VENV_UVICORN)) main:app --reload --port 8888

frontend:
	cd frontend && npm run dev

# ── Docker build ──────────────────────────────────────────────────────────────

build:
	bash docker/build.sh both

build-backend:
	bash docker/build.sh backend

build-frontend:
	bash docker/build.sh frontend

# ── Docker push ───────────────────────────────────────────────────────────────

push:
	bash docker/push.sh both

push-backend:
	bash docker/push.sh backend

push-frontend:
	bash docker/push.sh frontend

# ── Release (build + push) ────────────────────────────────────────────────────

release: build push

# ── Docker compose dev ────────────────────────────────────────────────────────

docker-dev:
	docker compose -f docker/docker-compose.dev.yml up --build

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	cd backend && $(abspath $(VENV_PYTEST)) tests/ -v

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	rm -rf frontend/dist
	find . -name "__pycache__" -type d -not -path '*/.venv/*' -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -type d -not -path '*/.venv/*' -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned build artifacts."
