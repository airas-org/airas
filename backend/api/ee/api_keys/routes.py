from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from airas.container import Container
from airas.infra.db.models.user_api_key import ApiProvider
from airas.usecases.ee.api_key_service import ApiKeyService
from api.ee.auth.dependencies import get_current_user_id
from api.schemas.ee import ApiKeyListResponse, ApiKeyResponse, SaveApiKeyRequest

router = APIRouter(prefix="/api-keys", tags=["ee-api-keys"])


@router.post("", response_model=ApiKeyResponse)
@inject
def save_api_key(
    request: SaveApiKeyRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ApiKeyService, Depends(Provide[Container.api_key_service])],
) -> ApiKeyResponse:
    service.save_key(
        user_id=current_user_id,
        provider=request.provider,
        api_key=request.api_key,
    )
    keys = service.list_keys(current_user_id)
    matched = next(k for k in keys if k["provider"] == request.provider)
    return ApiKeyResponse(**matched)


@router.get("", response_model=ApiKeyListResponse)
@inject
def list_api_keys(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ApiKeyService, Depends(Provide[Container.api_key_service])],
) -> ApiKeyListResponse:
    return ApiKeyListResponse(keys=service.list_keys(current_user_id))


@router.delete("/{provider}")
@inject
def delete_api_key(
    provider: ApiProvider,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ApiKeyService, Depends(Provide[Container.api_key_service])],
):
    deleted = service.delete_key(user_id=current_user_id, provider=provider)
    if not deleted:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"deleted": True}
