#!/bin/bash
set -e

echo "Generating OpenAPI schema..."
cd backend
if PYTHONPATH="$(pwd)/src" .venv/bin/python scripts/generate_openapi.py 2>/dev/null; then
  :
else
  uv run python scripts/generate_openapi.py
fi
cd ..

echo "Generating frontend API client..."
cd frontend && npm run generate-api
cd ..

echo "Adding generated files to staging..."
git add schema/openapi.yaml
git add frontend/src/lib/api/

echo "OpenAPI schema and frontend client updated successfully"
