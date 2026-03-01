from datetime import datetime, timezone
from uuid import UUID

from airas.infra.db.models.user_api_key import ApiProvider, UserApiKeyModel
from airas.infra.encryption import decrypt, encrypt
from airas.repository.user_api_key_repository import UserApiKeyRepository


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


class ApiKeyService:
    def __init__(self, repo: UserApiKeyRepository):
        self.repo = repo

    def save_key(
        self, *, user_id: UUID, provider: ApiProvider, api_key: str
    ) -> UserApiKeyModel:
        existing = self.repo.get_by_user_and_provider(user_id, provider)
        if existing:
            existing.encrypted_key = encrypt(api_key)
            existing.updated_at = datetime.now(timezone.utc)
            self.repo.db.add(existing)
            self.repo.db.commit()
            self.repo.db.refresh(existing)
            return existing
        model = UserApiKeyModel(
            user_id=user_id,
            provider=provider,
            encrypted_key=encrypt(api_key),
        )
        return self.repo.create(model)

    def list_keys(self, user_id: UUID) -> list[dict]:
        keys = self.repo.list_by_user(user_id)
        return [
            {
                "provider": k.provider,
                "masked_key": _mask_key(decrypt(k.encrypted_key)),
                "created_at": k.created_at,
                "updated_at": k.updated_at,
            }
            for k in keys
        ]

    def delete_key(self, *, user_id: UUID, provider: ApiProvider) -> bool:
        return self.repo.delete_by_user_and_provider(user_id, provider)

    def close(self) -> None:
        self.repo.db.close()
