from typing import Any, Generic, TypeVar

from sqlmodel import Session, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: type[T]):
        self.db = db
        self.model = model

    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def add(self, obj: T) -> T:
        return self.create(obj)

    def get(self, id_: Any) -> T | None:
        return self.db.get(self.model, id_)

    def list(self, *, offset: int = 0, limit: int | None = None) -> list[T]:
        statement = select(self.model).offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        return self.db.exec(statement).all()

    def update(self, id_: Any, **kwargs: Any) -> T | None:
        obj = self.get(id_)
        if obj is None:
            return None

        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id_: Any) -> bool:
        obj = self.get(id_)
        if obj is None:
            return False

        self.db.delete(obj)
        self.db.commit()
        return True
