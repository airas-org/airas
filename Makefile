# Local development commands:
#   make up       - Build and start all services
#   make down      - Stop all services
#   make logs      - Show service logs
#   make ps        - Show service status
#   make update-api- Regenerate OpenAPI and frontend client

SHELL := /bin/bash

COMPOSE ?= docker compose
COMPOSE_FILE ?= compose.yml
PROJECT ?= oss-webapp

BACKEND_SERVICE ?= backend

COMPOSE_CMD := $(COMPOSE) -f $(COMPOSE_FILE) -p $(PROJECT)

.PHONY: up down logs ps update-api generate-openapi ruff mypy biome

up:
	$(COMPOSE_CMD) up --build

down:
	$(COMPOSE_CMD) down

logs:
	$(COMPOSE_CMD) logs -f --tail=200

ps:
	$(COMPOSE_CMD) ps

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
