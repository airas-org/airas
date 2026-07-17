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

import contextlib
import json
import logging
import os
import tempfile
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


# Original os.environ values for keys this process has overridden from the
# file (None = the variable did not exist). Lets refresh_environment() undo
# an override once the key is removed from the file, so deletions take
# effect immediately too.
_overridden_originals: dict[str, str | None] = {}


def refresh_environment() -> None:
    """Sync credentials from the file into os.environ (file values win).

    Downstream code — LLM clients and subgraphs such as
    set_github_actions_secrets — resolves credentials from the
    environment, so injecting them here makes every path work. Keys that
    were previously injected but have since been removed from the file are
    restored to their original value (or unset).
    """
    credentials = load_credentials()
    for name, value in credentials.items():
        if name not in _overridden_originals:
            _overridden_originals[name] = os.environ.get(name)
        os.environ[name] = value
    for name in list(_overridden_originals):
        if name not in credentials:
            original = _overridden_originals.pop(name)
            if original is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = original


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
    # Optional: raise rate limits for the paper-search sources.
    CredentialSpec("SEMANTIC_SCHOLAR_API_KEY"),
    CredentialSpec("OPENALEX_API_KEY"),
    CredentialSpec("WANDB_API_KEY"),
    CredentialSpec("LANGFUSE_SECRET_KEY"),
    CredentialSpec("LANGFUSE_PUBLIC_KEY"),
    CredentialSpec("LANGFUSE_BASE_URL", is_secret=False),
    # Optional: run experiments on the AIXS compute platform.
    CredentialSpec("AIXS_API_KEY"),
    CredentialSpec("AIXS_BASE_URL", is_secret=False),
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
    # mkstemp creates the file with 0600 and a unique name, so the secrets
    # are never readable by other users and concurrent writers cannot
    # collide on a fixed temp path.
    fd, tmp_path = tempfile.mkstemp(
        dir=CREDENTIALS_PATH.parent, prefix=".credentials-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(existing, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, CREDENTIALS_PATH)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise
