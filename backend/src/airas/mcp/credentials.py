"""Credential loading for the AIRAS MCP server.

Credentials live in ``~/.airas/credentials.json`` — a flat JSON object
mapping credential names to values, e.g.::

    {
      "OPENAI_API_KEY": "sk-...",
      "GH_PERSONAL_ACCESS_TOKEN": "ghp_..."
    }

The file is re-read on every tool call that needs credentials, so edits
take effect immediately without restarting the server.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = Path("~/.airas/credentials.json").expanduser()

SETUP_INSTRUCTIONS = (
    f"Create {CREDENTIALS_PATH} containing your credentials, e.g. "
    '{"OPENAI_API_KEY": "sk-...", "GH_PERSONAL_ACCESS_TOKEN": "ghp_..."} '
    "(chmod 600 recommended). Edits take effect on the next tool call."
)


def load_credentials() -> dict[str, str]:
    """Read ~/.airas/credentials.json; returns {} if absent or invalid."""
    try:
        raw = json.loads(CREDENTIALS_PATH.read_text())
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError):
        logger.warning("Could not parse %s; ignoring it.", CREDENTIALS_PATH)
        return {}
    if not isinstance(raw, dict):
        logger.warning("%s must contain a JSON object; ignoring it.", CREDENTIALS_PATH)
        return {}
    return {k: v for k, v in raw.items() if isinstance(v, str) and v}


def refresh_environment() -> None:
    """Load credentials into os.environ (file values take precedence).

    Downstream code — LLM clients and subgraphs such as
    set_github_actions_secrets — resolves credentials from the
    environment, so injecting them here makes every path work.
    """
    os.environ.update(load_credentials())
