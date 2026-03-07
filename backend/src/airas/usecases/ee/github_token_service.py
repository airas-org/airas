from uuid import UUID

from airas.infra.encryption import decrypt, encrypt
from airas.repository.user_github_token_repository import UserGithubTokenRepository


class GitHubTokenService:
    def __init__(self, repo: UserGithubTokenRepository):
        self.repo = repo

    def save_token(self, user_id: UUID, github_token: str) -> None:
        self.repo.upsert(user_id, encrypt(github_token))

    def get_token(self, user_id: UUID) -> str | None:
        model = self.repo.get_by_user_id(user_id)
        if model is None:
            return None
        return decrypt(model.encrypted_token)
