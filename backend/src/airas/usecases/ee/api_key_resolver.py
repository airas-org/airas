"""Resolve LLM API keys based on user plan.

Non-EE: use API keys from environment variables directly.
EE Free users: use their own API keys stored in DB (encrypted).
EE Pro users: use platform-provided API keys from environment variables,
              with optional fallback to user-stored keys.

This module owns the full ``user_id + model -> api_key`` resolution chain.
"""

import logging
import os
from collections.abc import Callable
from uuid import UUID

from airas.infra.db.models.user_api_key import ApiProvider
from airas.infra.db.models.user_plan import PlanType
from airas.infra.encryption import decrypt
from airas.infra.llm_provider_resolver import PROVIDER_PRIMARY_KEY, infer_provider
from airas.repository.user_api_key_repository import UserApiKeyRepository
from airas.usecases.ee.plan_service import PlanService

logger = logging.getLogger(__name__)

# Mapping from ApiProvider to environment variable names
_PROVIDER_ENV_MAP: dict[ApiProvider, str] = {
    ApiProvider.OPENAI: "OPENAI_API_KEY",
    ApiProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    ApiProvider.GEMINI: "GEMINI_API_KEY",
}

# TODO: Provisional name. Rename once the paid plan is finalised.
_PLATFORM_API_KEY_ENV = "AIRAS_API_KEY"


class ApiKeyResolver:
    """Resolves API keys based on user plan type."""

    def __init__(
        self,
        plan_service: PlanService,
        api_key_repo: UserApiKeyRepository,
    ):
        self._plan_service = plan_service
        self._api_key_repo = api_key_repo

    def resolve_keys(self, user_id: UUID | None = None) -> dict[str, str]:
        """Return a dict of env_var_name -> api_key.

        - user_id is None (non-EE): read keys from environment variables directly.
        - EE paid plan: use platform-provided AIRAS_API_KEY,
          with fallback to user-stored keys for providers not covered.
        - EE Free: use user-stored DB keys only.
        """
        if user_id is None:
            return self._resolve_from_env()

        plan = self._plan_service.get_plan(user_id)
        match plan.plan_type:
            case PlanType.PRO:
                return self._resolve_platform_keys(user_id)
            case PlanType.FREE:
                return self._resolve_user_keys(user_id)
            case _ as unknown:
                raise ValueError(f"Unknown plan type: {unknown}")

    def create_key_fn(self, keys: dict[str, str]) -> Callable[[str], str | None]:
        def _resolve(model_name: str) -> str | None:
            provider = infer_provider(model_name)
            if provider is None:
                logger.warning(
                    f"Cannot infer provider for model '{model_name}'; no api_key will be injected."
                )
                return None
            env_var = PROVIDER_PRIMARY_KEY.get(provider)
            if env_var is None:
                return None
            return keys.get(env_var)

        return _resolve

    def _resolve_from_env(self) -> dict[str, str]:
        """Non-EE path: read API keys from plain environment variables."""
        keys: dict[str, str] = {}
        for _provider, env_name in _PROVIDER_ENV_MAP.items():
            val = os.getenv(env_name, "")
            if val:
                keys[env_name] = val
        return keys

    def _resolve_platform_keys(self, user_id: UUID) -> dict[str, str]:
        """EE paid plan: use platform-provided AIRAS_API_KEY, fallback to user keys.

        TODO: How AIRAS_API_KEY maps to individual providers is TBD.
        For now it is stored under every provider env-var name so that
        existing client code can pick it up regardless of provider.
        """
        keys: dict[str, str] = {}
        platform_key = os.getenv(_PLATFORM_API_KEY_ENV, "")
        if platform_key:
            for _provider, env_name in _PROVIDER_ENV_MAP.items():
                keys[env_name] = platform_key

        # Fallback: fill in providers not covered by platform key
        db_keys = self._api_key_repo.list_by_user(user_id)
        for db_key in db_keys:
            env_name = _PROVIDER_ENV_MAP.get(ApiProvider(db_key.provider))
            if env_name and env_name not in keys:
                keys[env_name] = decrypt(db_key.encrypted_key)

        return keys

    def _resolve_user_keys(self, user_id: UUID) -> dict[str, str]:
        """EE Free: user-stored DB keys only."""
        keys: dict[str, str] = {}
        db_keys = self._api_key_repo.list_by_user(user_id)
        for db_key in db_keys:
            env_name = _PROVIDER_ENV_MAP.get(ApiProvider(db_key.provider))
            if env_name:
                keys[env_name] = decrypt(db_key.encrypted_key)
        return keys
