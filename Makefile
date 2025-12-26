.PHONY: generate-openapi
update-api:
	cd backend && uv run python scripts/generate_openapi.py &&\
	cd ../frontend && npm run generate-api