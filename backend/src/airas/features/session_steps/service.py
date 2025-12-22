from typing import Any
from uuid import UUID

from sqlmodel import Session

from airas.types.session_step import SessionStepModel, SessionStepType


class SessionStepService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        session_id: UUID,
        step_type: SessionStepType,
        content: Any,
        schema_version: int,
        created_by: UUID,
        is_complated: bool,
    ) -> SessionStepModel:
        obj = SessionStepModel(
            session_id=session_id,
            step_type=step_type,
            content=content,
            schema_version=schema_version,
            created_by=created_by,
            is_complated=is_complated,
        )
        with self.db.begin():
            self.db.add(obj)
            self.db.flush()
        return obj

    def get(self, step_id: UUID) -> SessionStepModel:
        obj = self.db.get(SessionStepModel, step_id)
        if obj is None:
            raise ValueError("session step not found")
        return obj

    def close(self) -> None:
        self.db.close()
