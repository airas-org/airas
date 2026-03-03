"""Resolve LLM API keys based on user plan.

Free users: use their own API keys stored in DB (encrypted).
Pro users: use platform-provided API keys from environment variables.
"""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

from airas.infra.db.models.user_api_key import ApiProvider
from airas.infra.db.models.user_plan import PlanType
from airas.infra.encryption import decrypt
from airas.repository.user_api_key_repository import UserApiKeyRepository
from airas.repository.user_plan_repository import UserPlanRepository

logger = logging.getLogger(__name__)

# Mapping from ApiProvider to environment variable names
_PROVIDER_ENV_MAP: dict[ApiProvider, str] = {
    ApiProvider.OPENAI: "OPENAI_API_KEY",
    ApiProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    ApiProvider.GEMINI: "GEMINI_API_KEY",
}

# Platform keys are stored with this prefix in environment variables
_PLATFORM_KEY_PREFIX = "PLATFORM_"


class ApiKeyResolver:
    """Resolves API keys based on user plan type."""

    def __init__(
        self,
        plan_repo: UserPlanRepository,
        api_key_repo: UserApiKeyRepository,
    ):
        self._plan_repo = plan_repo
        self._api_key_repo = api_key_repo

    def resolve_keys(self, user_id: UUID) -> dict[str, str]:
        """Return a dict of env_var_name -> api_key for the given user.

        Pro users get platform-provided keys (PLATFORM_OPENAI_API_KEY etc.).
        Free users get their own DB-stored keys.
        """
        plan = self._plan_repo.get_by_user(user_id)
        is_pro = plan is not None and plan.plan_type == PlanType.PRO

        keys: dict[str, str] = {}

        if is_pro:
            for _provider, env_name in _PROVIDER_ENV_MAP.items():
                platform_key = os.getenv(f"{_PLATFORM_KEY_PREFIX}{env_name}", "")
                if platform_key:
                    keys[env_name] = platform_key
        else:
            db_keys = self._api_key_repo.list_by_user(user_id)
            for db_key in db_keys:
                env_name = _PROVIDER_ENV_MAP.get(ApiProvider(db_key.provider))
                if env_name:
                    keys[env_name] = decrypt(db_key.encrypted_key)

        return keys

    @contextmanager
    def inject_keys(self, user_id: UUID) -> Generator[None, None, None]:
        """Context manager that temporarily sets resolved API keys as env vars.

        Restores original values on exit.
        """
        resolved = self.resolve_keys(user_id)
        originals: dict[str, str | None] = {}

        for env_name, key_value in resolved.items():
            originals[env_name] = os.environ.get(env_name)
            os.environ[env_name] = key_value

        try:
            yield
        finally:
            for env_name, original in originals.items():
                if original is None:
                    os.environ.pop(env_name, None)
                else:
                    os.environ[env_name] = original

    def close(self) -> None:
        self._plan_repo.db.close()
