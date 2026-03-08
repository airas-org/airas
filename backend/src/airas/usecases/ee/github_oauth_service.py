import logging
import os
import secrets
from datetime import datetime, timezone

import httpx

from airas.infra.db.models.user_github_token import UserGitHubTokenModel
from airas.infra.encryption import decrypt, encrypt
from airas.repository.user_github_token_repository import UserGitHubTokenRepository

logger = logging.getLogger(__name__)


class GitHubOAuthService:
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"

    def __init__(self, repo: UserGitHubTokenRepository):
        self.repo = repo

    @staticmethod
    def _get_client_id() -> str:
        val = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
        if not val:
            raise RuntimeError("GITHUB_OAUTH_CLIENT_ID is not configured")
        return val

    @staticmethod
    def _get_client_secret() -> str:
        val = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
        if not val:
            raise RuntimeError("GITHUB_OAUTH_CLIENT_SECRET is not configured")
        return val

    @staticmethod
    def _get_redirect_uri(fallback: str) -> str:
        """Return fixed redirect URI from env var, or fallback to client-provided value."""
        return os.getenv("GITHUB_OAUTH_REDIRECT_URI", "") or fallback

    def get_authorize_url(self, redirect_uri: str) -> tuple[str, str]:
        """Return (authorize_url, state)."""
        from urllib.parse import urlencode

        state = secrets.token_urlsafe(32)
        params = {
            "client_id": self._get_client_id(),
            "redirect_uri": self._get_redirect_uri(redirect_uri),
            "scope": "repo",
            "state": state,
        }
        qs = urlencode(params)
        return f"{self.AUTHORIZE_URL}?{qs}", state

    async def exchange_code(self, *, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for access token and fetch user info."""
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self._get_client_id(),
                    "client_secret": self._get_client_secret(),
                    "code": code,
                    "redirect_uri": self._get_redirect_uri(redirect_uri),
                },
                headers={"Accept": "application/json"},
            )
            token_resp.raise_for_status()
            token_data = token_resp.json()

            if "error" in token_data:
                raise RuntimeError(
                    f"GitHub OAuth error: {token_data.get('error_description', token_data['error'])}"
                )

            access_token = token_data["access_token"]

            user_resp = await client.get(
                self.USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            user_resp.raise_for_status()
            user_data = user_resp.json()

        return {
            "access_token": access_token,
            "github_login": user_data["login"],
        }

    def save_token(
        self, *, session_token: str, access_token: str, github_login: str
    ) -> UserGitHubTokenModel:
        existing = self.repo.get_by_session_token(session_token)
        if existing:
            existing.encrypted_token = encrypt(access_token)
            existing.github_login = github_login
            existing.updated_at = datetime.now(timezone.utc)
            self.repo.db.add(existing)
            self.repo.db.commit()
            self.repo.db.refresh(existing)
            return existing
        model = UserGitHubTokenModel(
            session_token=session_token,
            encrypted_token=encrypt(access_token),
            github_login=github_login,
        )
        return self.repo.create(model)

    def get_status(self, session_token: str) -> dict | None:
        token_model = self.repo.get_by_session_token(session_token)
        if token_model is None:
            return None
        return {
            "github_login": token_model.github_login,
            "connected_at": token_model.created_at,
        }

    def disconnect(self, session_token: str) -> bool:
        return self.repo.delete_by_session_token(session_token)

    def get_token(self, session_token: str) -> str | None:
        """Return decrypted access token for the session, or None."""
        token_model = self.repo.get_by_session_token(session_token)
        if token_model is None:
            return None
        return decrypt(token_model.encrypted_token)
