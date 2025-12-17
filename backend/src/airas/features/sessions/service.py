from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from airas.domain.models.session import SessionModel


class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, title: str | None) -> SessionModel:
        obj = SessionModel(title=title)
        with self.db.begin():
            self.db.add(obj)
            self.db.flush()
        return obj

    def get(self, session_id: UUID) -> SessionModel:
        obj = self.db.get(SessionModel, session_id)
        if obj is None:
            raise ValueError("session not found")
        return obj
