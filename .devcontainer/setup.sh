#!/usr/bin/env bash
set -euo pipefail
set -x

cd "${containerWorkspaceFolder:-/workspaces/airas}"
uv python install 3.11
uv python pin 3.11
uv venv --python 3.11
uv sync

git config --global user.name "${GIT_USER_NAME:-Developer}"
git config --global user.email "${GIT_USER_EMAIL:-developer@example.com}"
git config --global init.defaultBranch main

uv run pre-commit install