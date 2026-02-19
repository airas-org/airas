from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from airas.infra.db.models.e2e import E2EModel, Status, StepType


@runtime_checkable
class TopicOpenEndedResearchServiceProtocol(Protocol):
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
    ) -> E2EModel: ...

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
    ) -> E2EModel: ...

    def get(self, id: UUID) -> E2EModel: ...

    def list(self, *, offset: int = 0, limit: int | None = None) -> list[E2EModel]: ...

    def delete(self, id: UUID) -> None: ...

    def close(self) -> None: ...
