#!/usr/bin/env bash
set -euo pipefail
set -x

# --- Backend (Python + uv) ---
cd /workspaces/airas/backend

# Ensure Python 3.11 is available via uv (idempotent)
uv python install 3.11
uv python pin 3.11

# Create venv if missing (idempotent-ish)
if [ ! -d ".venv" ]; then
  uv venv --python 3.11
fi

# Install deps (use lock if present)
uv sync

# Install git hooks (run from repo root, but use backend's uv project for the tool)
cd /workspaces/airas
uv run --project backend pre-commit install

# --- Frontend (Node + npm) ---
cd /workspaces/airas/frontend

# Prefer deterministic install if lockfile exists
if [ -f "package-lock.json" ]; then
  npm ci
else
  npm install
fi

set +x

# --- Load .env into shell profile ---
if [ -f /workspaces/airas/.env ]; then
  if ! grep -q "source /workspaces/airas/.env" ~/.bashrc 2>/dev/null; then
    echo 'set -a; source /workspaces/airas/.env; set +a' >> ~/.bashrc
  fi
fi

echo "[setup] done"
