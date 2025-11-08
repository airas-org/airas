#!/usr/bin/env bash
set -euo pipefail

cd "${containerWorkspaceFolder:-/workspaces/airas}"
uv python install 3.11
uv python pin 3.11
uv venv --python 3.11
uv sync
uv run pre-commit install
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --log-level debug --reload
