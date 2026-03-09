from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.verification import VerificationModel
from airas.repository.base_repository import BaseRepository


class VerificationRepository(BaseRepository[VerificationModel]):
    def __init__(self, db: Session):
        super().__init__(db, VerificationModel)

    def list_by_user(self, created_by: UUID) -> list[VerificationModel]:
        statement = select(VerificationModel).where(
            VerificationModel.created_by == created_by
        )
        return self.db.exec(statement).all()
