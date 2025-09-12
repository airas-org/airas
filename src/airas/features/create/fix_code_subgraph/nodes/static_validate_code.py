import json
import logging
import subprocess
import tempfile
from pathlib import Path

import toml
import yaml
from packaging.requirements import Requirement

logger = logging.getLogger(__name__)


def static_validate_code(
    generated_file_contents: dict[str, str],
) -> dict[str, dict[str, list[str]]]:
    file_validations: dict[str, dict[str, list[str]]] = {}

    logger.info("Starting static code validation...")

    for file_path, content in generated_file_contents.items():
        logger.info(f"Validating {file_path}")

        try:
            if file_path.endswith(".py"):
                file_errors, file_warnings = _validate_python_file(file_path, content)
            elif file_path == "pyproject.toml":
                file_errors, file_warnings = _validate_pyproject_toml(content)
            elif file_path.endswith((".yaml", ".yml")):
                file_errors, file_warnings = _validate_yaml_file(content)
            else:
                file_errors, file_warnings = [], []
        except Exception as e:
            file_errors = [f"Unexpected validation error in {file_path}: {str(e)}"]
            file_warnings = []

        file_validations[file_path] = {
            "errors": file_errors,
            "warnings": file_warnings,
        }

    total_errors = sum(len(fv.get("errors", [])) for fv in file_validations.values())
    total_warnings = sum(
        len(fv.get("warnings", [])) for fv in file_validations.values()
    )
    logger.info(
        f"Validation complete. Found {total_errors} errors, {total_warnings} warnings"
    )
    return file_validations


def _validate_python_file(file_path: str, content: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    ruff_errors, ruff_warnings = _run_ruff(file_path, content)
    errors.extend(ruff_errors)
    warnings.extend(ruff_warnings)

    if any("[E9" in error or "[F" in error for error in ruff_errors):
        logger.warning(f"Syntax errors found in {file_path}. Skipping further checks")
        return errors, warnings

    mypy_errors, mypy_warnings = _run_mypy(file_path, content)
    errors.extend(mypy_errors)
    warnings.extend(mypy_warnings)

    return errors, warnings


def _run_ruff(file_path: str, content: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        result = subprocess.run(
            [
                "ruff",
                "check",
                "--output-format=json",
                "--stdin-filename",
                file_path,
                "--silent",
                "-",
            ],
            input=content,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.stdout:
            issues = json.loads(result.stdout)
            for issue in issues:
                msg = f"Line {issue['location']['row']}: [{issue['code']}] {issue['message']}"
                if issue["code"].startswith(("F", "E9")):
                    errors.append(msg)
                else:
                    warnings.append(msg)

    except FileNotFoundError:
        warnings.append("Ruff not found. Skipping ruff check")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        warnings.append(f"Ruff check failed for {file_path}: {e}")

    return errors, warnings


def _run_mypy(file_path: str, content: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    tmp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = subprocess.run(
            ["mypy", tmp_path, "--ignore-missing-imports", "--no-site-packages"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            for line in result.stdout.split("\n"):
                if "error:" in line and tmp_path in line:
                    # Extract just the error message without file path
                    error_part = line.split("error:", 1)[-1].strip()
                    line_info = line.split(":")[1] if ":" in line else ""
                    if line_info.isdigit():
                        errors.append(f"Type error line {line_info}: {error_part}")
                    else:
                        errors.append(f"Type error: {error_part}")

    except FileNotFoundError:
        warnings.append("MyPy not found. Skipping type check")
    except (subprocess.TimeoutExpired, Exception) as e:
        warnings.append(f"MyPy check failed for {file_path}: {e}")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    return errors, warnings


def _validate_pyproject_toml(toml_content: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = toml.loads(toml_content)
        dependencies = data.get("project", {}).get("dependencies", [])

        if not isinstance(dependencies, list):
            return ["project.dependencies must be an array, not a mapping"], []

        for req_string in dependencies:
            try:
                # Only validate requirement string syntax
                Requirement(req_string)
            except Exception as e:
                errors.append(f"Invalid requirement '{req_string}': {e}")

    except toml.TomlDecodeError as e:
        errors.append(f"Invalid TOML: {e}")

    return errors, warnings


def _validate_yaml_file(content: str) -> tuple[list[str], list[str]]:
    try:
        yaml.safe_load(content)
        return [], []
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"], []


if __name__ == "__main__":
    test_cases = [
        # Test case 1: Valid files
        {
            "name": "Valid files",
            "files": {
                "src/main.py": """import numpy as np
import pandas as pd

def main():
    data = np.array([1, 2, 3])
    df = pd.DataFrame(data)
    print("Processing complete")

if __name__ == "__main__":
    main()
""",
                "pyproject.toml": """[project]
name = "test-project"
version = "0.1.0"
dependencies = [
    "numpy>=1.21.0",
    "pandas>=2.0.0"
]
""",
                "config/smoke_test.yaml": """
model:
  type: "linear"
  hidden_size: 128
data:
  batch_size: 32
training:
  epochs: 1
""",
                "config/full_experiment.yaml": """
model:
  type: "linear"
  hidden_size: 128
data:
  batch_size: 32
training:
  epochs: 50
""",
            },
        },
        # Test case 2: Python syntax errors
        {
            "name": "Python syntax errors",
            "files": {
                "src/broken.py": """import numpy as np

def broken_function(:  # Syntax error: missing parameter
    data = np.array([1, 2, 3])
    return data
""",
                "pyproject.toml": """[project]
name = "test-project"
version = "0.1.0"
dependencies = ["numpy>=1.21.0"]
""",
            },
        },
        # Test case 3: Invalid requirements
        {
            "name": "Invalid requirements",
            "files": {
                "src/main.py": """print("Hello World")""",
                "pyproject.toml": """[project]
name = "test-project"
version = "0.1.0"
dependencies = [
    "invalid-requirement->>><1.0.0"
]
""",
            },
        },
        # Test case 6: Invalid YAML
        {
            "name": "Invalid YAML",
            "files": {
                "config/smoke_test.yaml": """
invalid_yaml:
  key1: value1
  key2: [
    - item1
    - item2  # Invalid: mixing array syntax
"""
            },
        },
    ]

    print("=== Static Code Validation Test ===\n")
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 50)
        result = static_validate_code(test_case["files"])

        total_errors = sum(len(fv.get("errors", [])) for fv in result.values())
        total_warnings = sum(len(fv.get("warnings", [])) for fv in result.values())

        print(f"Total errors: {total_errors}, Total warnings: {total_warnings}")

        for file_path, validation in result.items():
            if validation["errors"] or validation["warnings"]:
                print(f"\n{file_path}:")
                for error in validation["errors"]:
                    print(f"  ERROR: {error}")
                for warning in validation["warnings"]:
                    print(f"  WARNING: {warning}")

        if total_errors == 0 and total_warnings == 0:
            print("✅ No issues found")

        print()
