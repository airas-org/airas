"""Credential storage shared by the MCP server and the dashboard.

Credentials live in ``~/.airas/credentials.json`` — a flat JSON object
mapping credential names to values, e.g.::

    {
      "OPENAI_API_KEY": "sk-...",
      "GH_PERSONAL_ACCESS_TOKEN": "ghp_..."
    }

The file is re-read on every use (MCP tool call / API request), so edits
take effect immediately without restarting anything. It can be edited by
hand or through the dashboard's settings page.
"""

import json
import logging
import os
import stat
from dataclasses import dataclass
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


@dataclass(frozen=True)
class CredentialSpec:
    name: str
    is_secret: bool = True


# Credentials the dashboard settings page manages. The file itself accepts
# arbitrary keys, but writes through the API are restricted to this list.
CREDENTIAL_SPECS: tuple[CredentialSpec, ...] = (
    CredentialSpec("GH_PERSONAL_ACCESS_TOKEN"),
    CredentialSpec("GITHUB_OWNER", is_secret=False),
    CredentialSpec("OPENAI_API_KEY"),
    CredentialSpec("ANTHROPIC_API_KEY"),
    CredentialSpec("GEMINI_API_KEY"),
    CredentialSpec("OPENROUTER_API_KEY"),
    CredentialSpec("AWS_BEARER_TOKEN_BEDROCK"),
    CredentialSpec("WANDB_API_KEY"),
    CredentialSpec("LANGFUSE_SECRET_KEY"),
    CredentialSpec("LANGFUSE_PUBLIC_KEY"),
    CredentialSpec("LANGFUSE_BASE_URL", is_secret=False),
)

KNOWN_CREDENTIAL_NAMES = frozenset(spec.name for spec in CREDENTIAL_SPECS)


def save_credentials(updates: dict[str, str]) -> None:
    """Merge `updates` into ~/.airas/credentials.json (0600).

    An empty-string value removes the credential. Keys already present in
    the file but absent from `updates` are left untouched, so unknown
    hand-added entries survive dashboard edits.
    """
    try:
        raw = json.loads(CREDENTIALS_PATH.read_text())
        existing = raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError):
        existing = {}

    for name, value in updates.items():
        if value:
            existing[name] = value
        else:
            existing.pop(name, None)

    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = CREDENTIALS_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(existing, indent=2) + "\n")
    tmp_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    tmp_path.replace(CREDENTIALS_PATH)
