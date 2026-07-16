from pydantic import BaseModel


class CredentialStatus(BaseModel):
    name: str
    is_secret: bool
    is_set: bool
    # Unmasked value for non-secret credentials; last 4 characters for secrets.
    preview: str | None = None


class ListCredentialsResponseBody(BaseModel):
    credentials: list[CredentialStatus]


class UpdateCredentialsRequestBody(BaseModel):
    # name -> value; an empty string removes the credential.
    updates: dict[str, str]


class UpdateCredentialsResponseBody(BaseModel):
    credentials: list[CredentialStatus]
