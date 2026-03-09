from __future__ import annotations

from datetime import datetime
from uuid import UUID

from airas.infra.db.models.verification import VerificationModel
from airas.repository.verification_repository import VerificationRepository


class VerificationService:
    def __init__(self, repo: VerificationRepository):
        self.repo = repo

    def create(
        self, *, created_by: UUID, title: str = "名称未設定"
    ) -> VerificationModel:
        verification = VerificationModel(title=title, created_by=created_by)
        return self.repo.create(verification)

    def get(self, id: UUID) -> VerificationModel | None:
        return self.repo.get(id)

    def list_by_user(self, created_by: UUID) -> list[VerificationModel]:
        return self.repo.list_by_user(created_by)

    def update(self, id: UUID, **kwargs: object) -> VerificationModel | None:
        kwargs["updated_at"] = datetime.now().astimezone()
        return self.repo.update(id, **kwargs)

    def delete(self, id: UUID) -> bool:
        return self.repo.delete(id)
