from sqlmodel import Session

from airas.infra.db.models.assisted_research_step import AssistedResearchStepModel
from airas.repository.base_repository import BaseRepository


class AssistedResearchStepRepository(BaseRepository[AssistedResearchStepModel]):
    def __init__(self, db: Session):
        super().__init__(db, AssistedResearchStepModel)
