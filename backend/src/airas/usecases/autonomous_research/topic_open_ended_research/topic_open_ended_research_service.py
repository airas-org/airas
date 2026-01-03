from datetime import datetime
from typing import Any
from uuid import UUID

from airas.infra.db.models.e2e import E2EModel, Status, StepType
from airas.repository.topic_open_ended_research_service_repository import (
    TopicOpenEndedResearchRepository,
)


class TopicOpenEndedResearchService:
    def __init__(self, repo: TopicOpenEndedResearchRepository):
        self.repo = repo

    def create(
        self,
        id: UUID,
        *,
        title: str,
        created_by: UUID,
        status: Status = Status.PENDING,
        current_step: StepType | None = None,
        error_message: str | None = None,
        result: dict[str, Any] | None = None,
        github_url: str | None = None,
    ) -> E2EModel:
        e2e = E2EModel(
            id=id,
            title=title,
            created_by=created_by,
            status=status,
            current_step=current_step,
            error_message=error_message,
            result=result or {},
            github_url=github_url,
        )
        return self.repo.create(e2e)

    def update(
        self,
        step_id: UUID,
        *,
        title: str | None = None,
        status: Status | None = None,
        current_step: StepType | None = None,
        error_message: str | None = None,
        result: dict[str, Any] | None = None,
        github_url: str | None = None,
    ) -> E2EModel:
        updates: dict[str, Any] = {}

        if title is not None:
            updates["title"] = title
        if status is not None:
            updates["status"] = status
        if current_step is not None:
            updates["current_step"] = current_step
        if error_message is not None:
            updates["error_message"] = error_message
        if result is not None:
            updates["result"] = result
        if github_url is not None:
            updates["github_url"] = github_url

        if updates:
            updates["last_updated_at"] = datetime.now().astimezone()

        updated = self.repo.update(step_id, **updates)
        if updated is None:
            raise ValueError("e2e result not found")
        return updated

    def get(self, step_id: UUID) -> E2EModel:
        step = self.repo.get(step_id)
        if step is None:
            raise ValueError("e2e result not found")
        return step

    def list(self, *, offset: int = 0, limit: int | None = None) -> list[E2EModel]:
        return self.repo.list(offset=offset, limit=limit)

    def delete(self, step_id: UUID) -> None:
        deleted = self.repo.delete(step_id)
        if not deleted:
            raise ValueError("e2e result not found")

    def close(self) -> None:
        self.repo.db.close()
