from __future__ import annotations

from datetime import datetime
from uuid import UUID

from airas.core.types.verification import VerificationModel


class VerificationService:
    """In-memory store for verification sessions."""

    def __init__(self) -> None:
        self._store: dict[UUID, VerificationModel] = {}

    def create(
        self, *, created_by: UUID, title: str = "名称未設定"
    ) -> VerificationModel:
        verification = VerificationModel(title=title, created_by=created_by)
        self._store[verification.id] = verification
        return verification

    def get(self, id: UUID) -> VerificationModel | None:
        return self._store.get(id)

    def list_by_user(self, created_by: UUID) -> list[VerificationModel]:
        return [v for v in self._store.values() if v.created_by == created_by]

    def update(self, id: UUID, **kwargs: object) -> VerificationModel | None:
        verification = self._store.get(id)
        if verification is None:
            return None
        for key, value in kwargs.items():
            setattr(verification, key, value)
        verification.updated_at = datetime.now().astimezone()
        return verification

    def delete(self, id: UUID) -> bool:
        return self._store.pop(id, None) is not None
