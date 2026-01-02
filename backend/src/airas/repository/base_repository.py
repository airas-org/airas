from typing import Generic, TypeVar

from sqlmodel import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: type[T]):
        self.db = db
        self.model = model

    def add(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()
        return obj

    def get(self, id_) -> T | None:
        return self.db.get(self.model, id_)
