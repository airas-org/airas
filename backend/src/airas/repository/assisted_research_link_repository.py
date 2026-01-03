from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.assisted_research_link import AssistedResearchLinkModel
from airas.repository.base_repository import BaseRepository


class AssistedResearchLinkRepository(BaseRepository[AssistedResearchLinkModel]):
    def __init__(self, db: Session):
        super().__init__(db, AssistedResearchLinkModel)

    def get_list(self, from_step_id: UUID) -> list[AssistedResearchLinkModel]:
        statement = select(AssistedResearchLinkModel).where(
            AssistedResearchLinkModel.from_step_id == from_step_id
        )
        return self.db.exec(statement).all()

    def get_by_from_to(
        self, *, from_step_id: UUID, to_step_id: UUID
    ) -> AssistedResearchLinkModel | None:
        statement = select(AssistedResearchLinkModel).where(
            AssistedResearchLinkModel.from_step_id == from_step_id,
            AssistedResearchLinkModel.to_step_id == to_step_id,
        )
        return self.db.exec(statement).first()
