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


class GitHubAuthorizeResponse(BaseModel):
    authorize_url: str
    state: str


class GitHubCallbackRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str


class GitHubConnectionStatus(BaseModel):
    connected: bool
    github_login: str | None = None
    connected_at: datetime | None = None


class GetMeResponse(BaseModel):
    user_id: str


class GitHubCallbackResponse(BaseModel):
    connected: bool
    github_login: str
    session_token: str


class GitHubDisconnectResponse(BaseModel):
    disconnected: bool


class GitHubProxyCompleteRequest(BaseModel):
    proxy_token: str


class CancelSubscriptionResponse(BaseModel):
    status: str


class WebhookReceivedResponse(BaseModel):
    received: bool
