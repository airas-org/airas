"""Shared OAuth Proxy for preview environments.

Provides the common logic needed to proxy OAuth callbacks through a fixed
production/develop backend so that preview environments (with dynamic URLs)
do not need their own callback URLs registered with each OAuth provider.

Service-specific classes (GitHub, Slack, Discord ...) hold an instance of
this class via composition and delegate proxy operations to it.
"""

import base64
import json
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

logger = logging.getLogger(__name__)


class OAuthProxyService:
    def _get_proxy_secret(self) -> str:
        if not (val := os.getenv("OAUTH_PROXY_SHARED_SECRET", "")):
            raise RuntimeError("OAUTH_PROXY_SHARED_SECRET is not configured")
        return val

    def get_develop_public_url(self) -> str:
        if not (val := os.getenv("DEVELOP_PUBLIC_URL", "")):
            raise RuntimeError("DEVELOP_PUBLIC_URL is not configured")
        return val.rstrip("/")

    def _get_allowed_origins_pattern(self) -> str:
        return os.getenv(
            "OAUTH_PROXY_ALLOWED_ORIGINS",
            r"https://airas.*\.vercel\.app",
        )

    def validate_origin(self, origin: str) -> None:
        if not origin.startswith("https://"):
            raise ValueError("Origin must use HTTPS")
        pattern = self._get_allowed_origins_pattern()
        if not re.fullmatch(pattern, origin):
            raise ValueError(f"Origin not allowed: {origin}")

    def encode_state(self, origin: str) -> str:
        self.validate_origin(origin)
        nonce = secrets.token_urlsafe(32)
        payload = json.dumps({"nonce": nonce, "origin": origin})
        return base64.urlsafe_b64encode(payload.encode()).decode()

    def decode_state(self, state: str) -> str:
        try:
            raw = base64.urlsafe_b64decode(state.encode())
            data = json.loads(raw)
            return data["origin"]
        except Exception as exc:
            raise ValueError(f"Invalid state parameter: {exc}") from exc

    def create_proxy_token(self, claims: dict[str, Any], ttl_minutes: int = 5) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            **claims,
            "iat": now,
            "exp": now + timedelta(minutes=ttl_minutes),
        }
        return jwt.encode(payload, self._get_proxy_secret(), algorithm="HS256")

    def validate_proxy_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._get_proxy_secret(), algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise ValueError("Proxy token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise ValueError(f"Invalid proxy token: {exc}") from exc
