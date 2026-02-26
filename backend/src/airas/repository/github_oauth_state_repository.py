from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.github_oauth_state import GitHubOAuthStateModel
from airas.repository.base_repository import BaseRepository


class GitHubOAuthStateRepository(BaseRepository[GitHubOAuthStateModel]):
    def __init__(self, db: Session):
        super().__init__(db, GitHubOAuthStateModel)

    def get_by_state(self, state: str) -> GitHubOAuthStateModel | None:
        statement = select(GitHubOAuthStateModel).where(
            GitHubOAuthStateModel.state == state
        )
        return self.db.exec(statement).first()

    def delete_by_state(self, state: str) -> bool:
        obj = self.get_by_state(state)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    def delete_expired(self, max_age_minutes: int = 10) -> int:
        """Delete OAuth states older than max_age_minutes."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=max_age_minutes)
        statement = select(GitHubOAuthStateModel).where(
            GitHubOAuthStateModel.created_at < cutoff
        )
        expired = self.db.exec(statement).all()
        count = len(expired)
        for obj in expired:
            self.db.delete(obj)
        if count > 0:
            self.db.commit()
        return count

    def delete_by_user_id(self, user_id: UUID) -> int:
        """Delete all OAuth states for a user."""
        statement = select(GitHubOAuthStateModel).where(
            GitHubOAuthStateModel.user_id == user_id
        )
        states = self.db.exec(statement).all()
        count = len(states)
        for obj in states:
            self.db.delete(obj)
        if count > 0:
            self.db.commit()
        return count
