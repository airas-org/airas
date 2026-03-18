from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from api.ee.auth.dependencies import get_current_user_id
from api.schemas.ee import GetMeResponse

router = APIRouter(prefix="/auth", tags=["ee-auth"])


@router.get("/me", response_model=GetMeResponse)
async def get_me(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> GetMeResponse:
    """Return the current authenticated user's ID."""
    return GetMeResponse(user_id=str(user_id))
