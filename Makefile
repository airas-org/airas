# Local development commands:
#   make up       - Build and start all services
#   make down      - Stop all services
#   make logs      - Show service logs
#   make ps        - Show service status
#   make migrate   - Apply database migrations
#   make db-reset  - Reset database (delete volumes)
#   make update-api- Regenerate OpenAPI and frontend client

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
	$(COMPOSE_CMD) up --build

down:
	$(COMPOSE_CMD) down

logs:
	$(COMPOSE_CMD) logs -f --tail=200

ps:
	$(COMPOSE_CMD) ps

migrate:
	$(COMPOSE_CMD) run --rm $(MIGRATE_SERVICE)

db-reset:
	$(COMPOSE_CMD) down -v
	$(COMPOSE_CMD) up -d $(DB_SERVICE)
	$(MAKE) migrate

update-api: generate-openapi

generate-openapi:
	cd backend && uv run python scripts/generate_openapi.py
	cd frontend && npm run generate-api

ruff:
	cd backend && ruff check --fix --show-fixes .
	cd backend && ruff format .

mypy:
	cd backend && mypy --config-file=pyproject.toml .

biome:
	cd frontend && npx biome check --write
