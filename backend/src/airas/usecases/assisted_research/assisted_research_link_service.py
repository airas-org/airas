from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from airas.infra.db.models.assisted_research_link import AssistedResearchLinkModel
from airas.repository.assisted_research_link_repository import (
    AssistedResearchLinkRepository,
)


class DuplicateAssistedResearchLinkError(ValueError):
    """Raised when an assisted research link already exists for the given steps."""


class AssistedResearchLinkService:
    def __init__(self, repo: AssistedResearchLinkRepository):
        self.repo = repo

    def create(
        self, *, from_step_id: UUID, to_step_id: UUID
    ) -> AssistedResearchLinkModel:
        existing = self.repo.get_by_from_to(
            from_step_id=from_step_id, to_step_id=to_step_id
        )
        if existing is not None:
            raise DuplicateAssistedResearchLinkError(
                "assisted research link already exists"
            )

        link = AssistedResearchLinkModel(
            from_step_id=from_step_id,
            to_step_id=to_step_id,
        )
        try:
            return self.repo.create(link)
        except IntegrityError as exc:
            # In case of race conditions, surface a user-friendly error.
            self.repo.db.rollback()
            raise DuplicateAssistedResearchLinkError(
                "assisted research link already exists"
            ) from exc

    def get_list(self, from_step_id: UUID) -> list[AssistedResearchLinkModel]:
        return self.repo.get_list(from_step_id)

    def close(self) -> None:
        self.repo.db.close()
