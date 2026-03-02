from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from airas.infra.db.models.user_api_key import ApiProvider
from airas.repository.user_api_key_repository import UserApiKeyRepository
from airas.usecases.ee.api_key_service import ApiKeyService
from api.ee.auth.dependencies import get_current_user_id
from api.ee.dependencies import EEDBSession
from api.schemas.ee import ApiKeyListResponse, ApiKeyResponse, SaveApiKeyRequest

router = APIRouter(prefix="/api-keys", tags=["ee-api-keys"])


@router.post("", response_model=ApiKeyResponse)
def save_api_key(
    request: SaveApiKeyRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: EEDBSession,
) -> ApiKeyResponse:
    repo = UserApiKeyRepository(db=db)
    service = ApiKeyService(repo=repo)
    service.save_key(
        user_id=current_user_id,
        provider=request.provider,
        api_key=request.api_key,
    )
    keys = service.list_keys(current_user_id)
    matched = next(k for k in keys if k["provider"] == request.provider)
    return ApiKeyResponse(**matched)


@router.get("", response_model=ApiKeyListResponse)
def list_api_keys(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: EEDBSession,
) -> ApiKeyListResponse:
    repo = UserApiKeyRepository(db=db)
    service = ApiKeyService(repo=repo)
    return ApiKeyListResponse(keys=service.list_keys(current_user_id))


@router.delete("/{provider}")
def delete_api_key(
    provider: ApiProvider,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: EEDBSession,
):
    repo = UserApiKeyRepository(db=db)
    service = ApiKeyService(repo=repo)
    deleted = service.delete_key(user_id=current_user_id, provider=provider)
    if not deleted:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"deleted": True}
