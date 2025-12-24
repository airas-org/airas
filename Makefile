.PHONY: generate-openapi
generate-openapi:
	cd backend && uv run python scripts/generate_openapi.py
