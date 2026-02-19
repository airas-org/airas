from datetime import datetime
from typing import Any
from uuid import UUID

from airas.infra.db.models.e2e import E2EModel, Status, StepType


class InMemoryTopicOpenEndedResearchService:
    def __init__(self) -> None:
        self._store: dict[UUID, E2EModel] = {}

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
        now = datetime.now().astimezone()
        e2e = E2EModel(
            id=id,
            title=title,
            created_by=created_by,
            status=status,
            current_step=current_step,
            error_message=error_message,
            result=result or {},
            github_url=github_url,
            created_at=now,
            last_updated_at=now,
            schema_version=1,
        )
        self._store[id] = e2e
        return e2e

    def update(
        self,
        id: UUID,
        *,
        title: str | None = None,
        status: Status | None = None,
        current_step: StepType | None = None,
        error_message: str | None = None,
        result: dict[str, Any] | None = None,
        github_url: str | None = None,
    ) -> E2EModel:
        e2e = self._store.get(id)
        if e2e is None:
            raise ValueError("e2e result not found")

        if title is not None:
            e2e.title = title
        if status is not None:
            e2e.status = status
        if current_step is not None:
            e2e.current_step = current_step
        if error_message is not None:
            e2e.error_message = error_message
        if result is not None:
            e2e.result = result
        if github_url is not None:
            e2e.github_url = github_url

        e2e.last_updated_at = datetime.now().astimezone()
        return e2e

    def get(self, id: UUID) -> E2EModel:
        e2e = self._store.get(id)
        if e2e is None:
            raise ValueError("e2e result not found")
        return e2e

    def list(self, *, offset: int = 0, limit: int | None = None) -> list[E2EModel]:
        items = list(self._store.values())
        items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items

    def delete(self, id: UUID) -> None:
        if id not in self._store:
            raise ValueError("e2e result not found")
        del self._store[id]

    def close(self) -> None:
        pass
