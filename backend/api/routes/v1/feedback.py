from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Closing, Provide, inject
from fastapi import APIRouter, Depends

from airas.container import Container
from airas.usecases.ee.feedback_service import FeedbackService
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.feedback import CreateFeedbackRequestBody, CreateFeedbackResponseBody

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=CreateFeedbackResponseBody)
@inject
def create_feedback(
    request: CreateFeedbackRequestBody,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    feedback_service: Annotated[
        FeedbackService,
        Depends(Closing[Provide[Container.feedback_service]]),
    ],
) -> CreateFeedbackResponseBody:
    feedback = feedback_service.create(
        created_by=current_user_id,
        category=request.category,
        subject=request.subject,
        detail=request.detail,
        email=request.email,
    )
    return CreateFeedbackResponseBody(
        id=str(feedback.id),
        category=feedback.category,
        subject=feedback.subject,
        detail=feedback.detail,
        email=feedback.email,
        created_at=feedback.created_at.isoformat(),
    )
