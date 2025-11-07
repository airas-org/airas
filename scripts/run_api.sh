set -Eeuo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
APP_IMPORT="${APP_IMPORT:-api.main:app}"
LOG_LEVEL="${LOG_LEVEL:-info}"

ARGS=(
  "$APP_IMPORT"
  --host "$HOST"
  --port "$PORT"
  --log-level "$LOG_LEVEL"
)


echo "[run_api] start: uv run uvicorn ${ARGS[*]}"
exec uv run uvicorn --reload "${ARGS[@]}"
