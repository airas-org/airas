from uuid import UUID

from sqlmodel import Session

from airas.core.db import get_db_session


def get_db() -> Session:
    return next(get_db_session())


def get_current_user_id() -> UUID:
    # 最小構成: 認証導入まで固定値でOK（後でJWT等に置き換え）
    return UUID("00000000-0000-0000-0000-000000000001")
