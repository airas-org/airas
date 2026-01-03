from sqlmodel import Session

from airas.infra.db.models.e2e import E2EModel
from airas.repository.base_repository import BaseRepository


class TopicOpenEndedResearchRepository(BaseRepository[E2EModel]):
    def __init__(self, db: Session):
        super().__init__(db, E2EModel)
