from uuid import UUID

from pydantic import BaseModel


class StepRunLinkCreateRequest(BaseModel):
    from_step_run_id: UUID
    to_step_run_id: UUID


class StepRunLinkResponse(BaseModel):
    from_step_run_id: UUID
    to_step_run_id: UUID


class StepRunLinkListResponse(BaseModel):
    links: list[StepRunLinkResponse]
