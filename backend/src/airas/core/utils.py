from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Mapping, Sequence
from uuid import UUID

from pydantic import BaseModel

JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | dict[str, "JSONValue"] | list["JSONValue"]


def _sanitize_string(s: str) -> str:
    """Remove null characters that PostgreSQL JSONB cannot handle."""
    return s.replace("\x00", "")


def to_dict_deep(obj: Any) -> Any:
    """
    - TypedDict/dict/list/tuple を再帰的に処理
    - Pydantic BaseModel は model_dump()（v2）で dict 化
    - Enum / datetime / UUID 等は JSON 互換に寄せる（必要に応じて）
    - 文字列から PostgreSQL JSONB で扱えないヌル文字を除去
    """
    if isinstance(obj, str):
        return _sanitize_string(obj)

    # Pydantic BaseModel（v2）
    if isinstance(obj, BaseModel):
        # mode="python" にすると datetime/UUID が生で残る（DB/JSONB向き）
        # mode="json" にすると ISO 文字列等に変換される（JSON API向き）
        dumped = obj.model_dump(mode="python")
        return to_dict_deep(dumped)

    # Mapping（dict等）
    if isinstance(obj, Mapping):
        return {str(k): to_dict_deep(v) for k, v in obj.items()}

    # Sequence（list/tuple等）ただし str/bytes は除外
    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        return [to_dict_deep(v) for v in obj]

    # Enum は値 or 名前へ（好みで統一）
    if isinstance(obj, Enum):
        return obj.value

    # JSONに寄せたい代表型（必要に応じて）
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)

    return obj
