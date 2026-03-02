"""Request-scoped DB session for EE routes.

Each call yields a fresh SQLModel Session that is automatically closed
when the request finishes, preventing connection pool exhaustion.
"""

from collections.abc import Generator
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from airas.container import Container


@inject
def get_ee_db_session(
    factory: Annotated[sessionmaker, Depends(Provide[Container.session_factory])],
) -> Generator[Session, None, None]:
    session: Session = factory()
    try:
        yield session
    finally:
        session.close()


EEDBSession = Annotated[Session, Depends(get_ee_db_session)]
