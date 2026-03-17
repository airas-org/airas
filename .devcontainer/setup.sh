#!/usr/bin/env bash
set -euo pipefail
set -x

WORKSPACE=/workspaces/airas
BACKEND="$WORKSPACE/backend"
FRONTEND="$WORKSPACE/frontend"

UV_VENV_DIR=/home/developer/.venvs/airas

# --- Backend (Python + uv) ---
cd "$BACKEND"

# Ensure Python 3.11 is available via uv (idempotent)
uv python install 3.11
uv python pin 3.11

# Create venv if missing or broken
if [ ! -x "$UV_VENV_DIR/bin/python" ]; then
    rm -rf "$UV_VENV_DIR"
    uv venv --python 3.11 "$UV_VENV_DIR"
fi

# Install dependencies (use lock if present)
uv sync

# Install git hooks (run from repo root, but use backend's uv project for the tool)
cd "$WORKSPACE"
git config --local --unset-all core.hooksPath 2>/dev/null || true

uv run --project backend pre-commit install --overwrite

# --- Frontend (Node + npm) ---
cd "$FRONTEND"

# Prefer deterministic install if lockfile exists
if [ -f "package-lock.json" ]; then
  npm ci
else
  npm install
fi

# --- Load .env into shell profile ---
set +x
if [ -f "$WORKSPACE/.env" ]; then
    if ! grep -q "source $WORKSPACE/.env" ~/.bashrc 2>/dev/null; then
        echo "set -a; source $WORKSPACE/.env; set +a" >> ~/.bashrc
    fi
fi

echo "[setup] done"
