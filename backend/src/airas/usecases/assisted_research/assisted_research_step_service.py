from typing import Any
from uuid import UUID

from airas.infra.db.models.assisted_research_step import AssistedResearchStepModel
from airas.infra.db.models.e2e import Status, StepType
from airas.repository.assisted_research_step_repository import (
    AssistedResearchStepRepository,
)


class AssistedResearchStepService:
    def __init__(self, repo: AssistedResearchStepRepository):
        self.repo = repo

    def create(
        self,
        *,
        session_id: UUID,
        created_by: UUID,
        status: Status,
        step_type: StepType,
        error_message: str | None,
        result: Any,
        schema_version: int,
    ) -> AssistedResearchStepModel:
        step = AssistedResearchStepModel(
            session_id=session_id,
            created_by=created_by,
            status=status,
            step_type=step_type,
            error_message=error_message,
            result=result,
            schema_version=schema_version,
        )
        return self.repo.create(step)

    def get(self, step_id: UUID) -> AssistedResearchStepModel:
        step = self.repo.get(step_id)
        if step is None:
            raise ValueError("session step not found")
        return step

    def list(
        self, *, offset: int = 0, limit: int | None = None
    ) -> list[AssistedResearchStepModel]:
        return self.repo.list(offset=offset, limit=limit)

    def close(self) -> None:
        self.repo.db.close()
