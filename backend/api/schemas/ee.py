from datetime import datetime

from pydantic import BaseModel

from airas.infra.db.models.user_api_key import ApiProvider


class SaveApiKeyRequest(BaseModel):
    provider: ApiProvider
    api_key: str


class ApiKeyResponse(BaseModel):
    provider: ApiProvider
    masked_key: str
    created_at: datetime
    updated_at: datetime


class ApiKeyListResponse(BaseModel):
    keys: list[ApiKeyResponse]


class UserPlanResponse(BaseModel):
    plan_type: str
    status: str
    stripe_customer_id: str | None = None
    requires_api_keys: bool = True


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str
