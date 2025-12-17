import os
from typing import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required (Postgres only).")

engine: Engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_db_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
