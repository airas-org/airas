from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends

from airas.core.container import Container
from airas.features.step_run_links.service import StepRunLinkService
from api.schemas.step_run_links import (
    StepRunLinkCreateRequest,
    StepRunLinkListResponse,
    StepRunLinkResponse,
)

router = APIRouter(prefix="/step-run-links", tags=["step-run-links"])


@router.post("", response_model=StepRunLinkResponse)
@inject
def create_step_run_link(
    request: StepRunLinkCreateRequest,
    svc: Annotated[
        StepRunLinkService, Depends(Closing[Provide[Container.step_run_link_service]])
    ],
) -> StepRunLinkResponse:
    link = svc.create(
        from_step_run_id=request.from_step_run_id,
        to_step_run_id=request.to_step_run_id,
    )
    return StepRunLinkResponse(
        from_step_run_id=link.from_step_run_id,
        to_step_run_id=link.to_step_run_id,
    )


@router.get("/{from_step_run_id}", response_model=StepRunLinkListResponse)
@inject
def list_step_run_links_by_from_step_run_id(
    from_step_run_id: UUID,
    svc: Annotated[
        StepRunLinkService, Depends(Closing[Provide[Container.step_run_link_service]])
    ],
) -> StepRunLinkListResponse:
    links = svc.list_by_from_step_run_id(from_step_run_id)
    return StepRunLinkListResponse(
        links=[
            StepRunLinkResponse(
                from_step_run_id=link.from_step_run_id,
                to_step_run_id=link.to_step_run_id,
            )
            for link in links
        ]
    )
