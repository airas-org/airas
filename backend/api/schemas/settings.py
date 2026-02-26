from pydantic import BaseModel


class SaveGitHubTokenRequest(BaseModel):
    github_token: str


class GitHubSettingsResponse(BaseModel):
    is_connected: bool
    github_username: str | None = None
    token_last4: str | None = None


class GitHubConnectionStatusResponse(BaseModel):
    is_valid: bool
    github_username: str | None = None
    error: str | None = None
