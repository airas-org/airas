"""Generate OpenAPI schema from FastAPI app and save to YAML file."""

import sys
from pathlib import Path

import yaml

# Add backend directory to path to import api.main
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from api.main import app  # noqa: E402


def generate_openapi_schema(output_path: Path) -> None:
    """Generate OpenAPI schema from FastAPI app and save to YAML file."""
    # Get OpenAPI schema as dict
    openapi_schema = app.openapi()

    # Convert to YAML and save
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            openapi_schema,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    print(f"OpenAPI schema generated successfully: {output_path}")


if __name__ == "__main__":
    # Output path: schema/openapi.yaml (relative to project root)
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "schema" / "openapi.yaml"

    # Create schema directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_openapi_schema(output_path)
