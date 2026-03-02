"""Request-scoped DB session for EE routes.

Each call yields a fresh SQLModel Session that is automatically closed
when the request finishes, preventing connection pool exhaustion.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from airas.container import container


def get_ee_db_session() -> Generator[Session, None, None]:
    factory = container.session_factory()
    session: Session = factory()
    try:
        yield session
    finally:
        session.close()


EEDBSession = Annotated[Session, Depends(get_ee_db_session)]
