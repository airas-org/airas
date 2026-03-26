"""Shared OAuth Proxy for preview environments.

Provides the common logic needed to proxy OAuth callbacks through a fixed
production/develop backend so that preview environments (with dynamic URLs)
do not need their own callback URLs registered with each OAuth provider.

Service-specific classes (GitHub, Slack, Discord ...) hold an instance of
this class via composition and delegate proxy operations to it.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class OAuthProxyService:
    def _get_proxy_secret(self) -> str:
        if not (val := os.getenv("OAUTH_PROXY_SHARED_SECRET", "")):
            raise RuntimeError("OAUTH_PROXY_SHARED_SECRET is not configured")
        return val

    def _get_fernet(self) -> Fernet:
        key_bytes = hashlib.sha256(self._get_proxy_secret().encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)

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

    # ---- state helpers (HMAC-signed) ----

    def encode_state(self, origin: str) -> str:
        self.validate_origin(origin)
        nonce = secrets.token_urlsafe(32)
        payload = json.dumps({"nonce": nonce, "origin": origin})
        sig = hmac.new(
            self._get_proxy_secret().encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        combined = json.dumps({"payload": payload, "sig": sig})

        return base64.urlsafe_b64encode(combined.encode()).decode()

    def decode_state(self, state: str) -> str:
        try:
            raw = base64.urlsafe_b64decode(state.encode())
            combined = json.loads(raw)
            payload = combined["payload"]
            sig = combined["sig"]
        except Exception as exc:
            raise ValueError(f"Invalid state parameter: {exc}") from exc

        expected_sig = hmac.new(
            self._get_proxy_secret().encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            raise ValueError("State signature verification failed")

        data = json.loads(payload)
        origin = data["origin"]
        self.validate_origin(origin)
        return origin

    # ---- proxy token (Fernet-encrypted) ----

    def create_proxy_token(self, claims: dict[str, Any], ttl_minutes: int = 5) -> str:
        claims["_exp"] = int(time.time()) + ttl_minutes * 60
        plaintext = json.dumps(claims).encode()
        return self._get_fernet().encrypt(plaintext).decode()

    def validate_proxy_token(self, token: str) -> dict[str, Any]:
        try:
            plaintext = self._get_fernet().decrypt(token.encode())
        except InvalidToken as exc:
            raise ValueError("Invalid or expired proxy token") from exc

        claims = json.loads(plaintext)
        if time.time() > claims.get("_exp", 0):
            raise ValueError("Proxy token has expired")
        claims.pop("_exp", None)
        return claims
