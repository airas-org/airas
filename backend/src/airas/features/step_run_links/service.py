from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from airas.types.step_run_link import StepRunLinkModel


class StepRunLinkService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, *, from_step_run_id: UUID, to_step_run_id: UUID
    ) -> StepRunLinkModel:
        obj = StepRunLinkModel(
            from_step_run_id=from_step_run_id,
            to_step_run_id=to_step_run_id,
        )
        with self.db.begin():
            self.db.add(obj)
            self.db.flush()
        return obj

    def list_by_from_step_run_id(
        self, from_step_run_id: UUID
    ) -> list[StepRunLinkModel]:
        statement = select(StepRunLinkModel).where(
            StepRunLinkModel.from_step_run_id == from_step_run_id
        )
        return list(self.db.execute(statement).scalars().all())

    def close(self) -> None:
        self.db.close()
