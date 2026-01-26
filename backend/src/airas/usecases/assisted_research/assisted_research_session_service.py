from __future__ import annotations

from uuid import UUID

from airas.infra.db.models.assisted_research_session import AssistedResearchSessionModel
from airas.repository.assisted_research_session_repository import (
    AssistedResearchSessionRepository,
)


class AssistedResearchSessionService:
    def __init__(self, repo: AssistedResearchSessionRepository):
        self.repo = repo

    def create(self, *, title: str, created_by: UUID) -> AssistedResearchSessionModel:
        session = AssistedResearchSessionModel(title=title, created_by=created_by)
        return self.repo.create(session)

    def get(self, session_id: UUID) -> AssistedResearchSessionModel:
        session = self.repo.get(session_id)
        if session is None:
            raise ValueError("session not found")
        return session

    def list(
        self, *, offset: int = 0, limit: int | None = None
    ) -> list[AssistedResearchSessionModel]:
        return self.repo.list(offset=offset, limit=limit)

    def close(self) -> None:
        self.repo.db.close()
