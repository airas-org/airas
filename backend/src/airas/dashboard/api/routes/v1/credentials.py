from fastapi import APIRouter, HTTPException, status

from airas.core.credentials import (
    CREDENTIAL_SPECS,
    KNOWN_CREDENTIAL_NAMES,
    load_credentials,
    save_credentials,
)
from airas.dashboard.api.schemas.credentials import (
    CredentialStatus,
    ListCredentialsResponseBody,
    UpdateCredentialsRequestBody,
    UpdateCredentialsResponseBody,
)

router = APIRouter(prefix="/credentials", tags=["credentials"])


def _statuses() -> list[CredentialStatus]:
    values = load_credentials()
    statuses = []
    for spec in CREDENTIAL_SPECS:
        value = values.get(spec.name, "")
        if not value:
            preview = None
        elif spec.is_secret:
            preview = f"...{value[-4:]}" if len(value) > 4 else "****"
        else:
            preview = value
        statuses.append(
            CredentialStatus(
                name=spec.name,
                is_secret=spec.is_secret,
                is_set=bool(value),
                preview=preview,
            )
        )
    return statuses


@router.get("", response_model=ListCredentialsResponseBody)
def list_credentials() -> ListCredentialsResponseBody:
    """Report which credentials are configured (values are never returned in full for secrets)."""
    return ListCredentialsResponseBody(credentials=_statuses())


@router.put("", response_model=UpdateCredentialsResponseBody)
def update_credentials(
    request: UpdateCredentialsRequestBody,
) -> UpdateCredentialsResponseBody:
    """Merge credential updates into ~/.airas/credentials.json.

    An empty-string value removes the credential. Only known credential
    names are accepted.
    """
    unknown = sorted(set(request.updates) - KNOWN_CREDENTIAL_NAMES)
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown credential names: {', '.join(unknown)}",
        )
    save_credentials(request.updates)
    return UpdateCredentialsResponseBody(credentials=_statuses())
