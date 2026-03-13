# Local development commands (devcontainer mode, DB provided by devcontainer):
#   make up        - Start backend (port 8000) and frontend (port 5173)
#   make down      - Stop backend and frontend processes
#   make ps        - Show running status of backend and frontend
#   make migrate   - (no-op: tables are created automatically on backend startup)
#   make db-reset  - (not supported in devcontainer mode)
#   make update-api- Regenerate OpenAPI schema and frontend client

SHELL := /bin/bash

COMPOSE ?= docker compose
COMPOSE_FILE ?= compose.yml
PROJECT ?= oss-webapp

BACKEND_SERVICE ?= backend
DB_SERVICE ?= db
MIGRATE_SERVICE ?= migrate

COMPOSE_CMD := $(COMPOSE) -f $(COMPOSE_FILE) -p $(PROJECT)

.PHONY: up down logs ps migrate db-reset update-api generate-openapi ruff mypy biome

up:
	@echo "Starting backend and frontend locally (DB is provided by devcontainer)..."
	@trap 'kill 0' EXIT; \
	(cd backend && uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload) & \
	(cd frontend && npm run dev) & \
	wait

down:
	@echo "Stopping local processes..."
	@pkill -f "uvicorn api.main:app" 2>/dev/null || true
	@pkill -f "vite" 2>/dev/null || true
	@echo "Done."

logs:
	$(COMPOSE_CMD) logs -f --tail=200

ps:
	@echo "=== Backend ===" && pgrep -a -f "uvicorn api.main:app" || echo "not running"
	@echo "=== Frontend ===" && pgrep -a -f "vite" || echo "not running"

migrate:
	@echo "Tables are created automatically by SQLModel.metadata.create_all() on backend startup."

db-reset:
	@echo "db-reset is not supported in devcontainer mode."
	@echo "To reset: drop and recreate the airas database from a PostgreSQL client."

update-api: generate-openapi

generate-openapi:
	cd backend && uv run python scripts/generate_openapi.py
	cd frontend && npm run generate-api

ruff:
	cd backend && uv run ruff check --fix --show-fixes .
	cd backend && uv run ruff format .

mypy:
	cd backend && uv run mypy .

biome:
	cd frontend && npx biome check .
