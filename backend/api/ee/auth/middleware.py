import logging
from uuid import UUID

import jwt
from fastapi import HTTPException, Request, status

from api.ee.settings import get_ee_settings

logger = logging.getLogger(__name__)

_jwks_client: jwt.PyJWKClient | None = None


def _get_jwks_client(supabase_url: str) -> jwt.PyJWKClient:
    """Return a cached JWKS client for the Supabase project."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = jwt.PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def verify_jwt(token: str) -> dict:
    """Verify Supabase JWT and return payload.

    Supabase may sign tokens with either HS256 (symmetric) or ES256 (asymmetric).
    We inspect the token header to choose the appropriate verification strategy.
    """
    settings = get_ee_settings()
    if not settings.supabase_url:
        logger.error("SUPABASE_URL is not configured but ENTERPRISE_ENABLED is true")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured on this server",
        )
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "")
        logger.info("JWT header alg=%s kid=%s", alg, header.get("kid", "N/A"))

        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                logger.error("SUPABASE_JWT_SECRET is required for HS256 tokens")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication is not configured on this server",
                )
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            jwks_client = _get_jwks_client(settings.supabase_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
            )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc
    except jwt.InvalidAudienceError as exc:
        logger.warning("JWT audience mismatch: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: audience mismatch",
        ) from exc
    except jwt.InvalidSignatureError as exc:
        logger.warning("JWT signature verification failed – check SUPABASE_JWT_SECRET")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: signature verification failed",
        ) from exc
    except jwt.InvalidTokenError as exc:
        logger.warning("JWT validation error (%s): %s", type(exc).__name__, exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


def extract_user_id_from_request(request: Request) -> UUID:
    """Extract and verify user ID from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = auth_header.removeprefix("Bearer ")
    payload = verify_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim",
        )
    return UUID(sub)
