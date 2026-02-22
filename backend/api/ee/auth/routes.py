from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from api.ee.auth.dependencies import get_current_user_id

router = APIRouter(prefix="/auth", tags=["ee-auth"])


@router.get("/me")
async def get_me(user_id: Annotated[UUID, Depends(get_current_user_id)]):
    """Return the current authenticated user's ID."""
    return {"user_id": str(user_id)}
