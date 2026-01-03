from sqlmodel import Session

from airas.infra.db.models.assisted_research_session import AssistedResearchSessionModel
from airas.repository.base_repository import BaseRepository


class AssistedResearchSessionRepository(BaseRepository[AssistedResearchSessionModel]):
    def __init__(self, db: Session):
        super().__init__(db, AssistedResearchSessionModel)
