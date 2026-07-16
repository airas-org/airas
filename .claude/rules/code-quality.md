## Code Quality

Lint hooks are defined in `.pre-commit-config.yaml` and run automatically on
commit (`pre-commit install` once per clone). Manual runs:

- `pre-commit run ruff --all-files` - Python linter, auto-fix, and formatter (backend/)
- `pre-commit run mypy --all-files` - Python type checking (backend/)
- `pre-commit run biome --all-files` - JavaScript/TypeScript linter and formatter (frontend/)
- `pre-commit run --all-files` - everything, including OpenAPI/client regeneration
