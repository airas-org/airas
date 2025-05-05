import os

import nox

# For local use (Python path for uv management)
local_python_versions = [
    "/root/.local/share/uv/python/cpython-3.10.17-linux-aarch64-gnu/bin/python3.10",
    "/root/.local/share/uv/python/cpython-3.11.12-linux-aarch64-gnu/bin/python3.11",
    "/root/.local/share/uv/python/cpython-3.12.10-linux-aarch64-gnu/bin/python3.12",
    "/root/.local/share/uv/python/cpython-3.13.3-linux-aarch64-gnu/bin/python3.13",
]

# Determine if it is a GitHub Actions or not by environment variables.
if os.getenv("GITHUB_ACTIONS") == "true":
    python_versions = ["3.10", "3.11", "3.12", "3.13"]
else:
    python_versions = local_python_versions


@nox.session(venv_backend="uv", python=python_versions)
def tests(session):
    session.run("uv", "pip", "install", "-e", ".", external=True)

    session.env["PYTHONPATH"] = "src"
    session.run(
        "pytest",
        "--cov=src/airas",
        "--cov-branch",
        "--cov-report=term-missing",
        "-v",
        "tests/",
        external=True,
    )
