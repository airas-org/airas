from __future__ import annotations

import math
import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Mapping, Sequence
from uuid import UUID

import numpy as np
from pydantic import BaseModel

JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | dict[str, "JSONValue"] | list["JSONValue"]


def _sanitize_string(s: str) -> str:
    """
    Sanitize string for PostgreSQL JSONB storage.

    PostgreSQL JSONB cannot handle certain control characters and invalid UTF-8 sequences.
    This function removes problematic characters and handles encoding issues.

    Process:
    1. Remove control characters (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F, 0x7F) that are invalid in JSONB
    2. Handle surrogate pairs and invalid UTF-8 sequences by replacing them with U+FFFD (�)

    Args:
        s: Input string to sanitize

    Returns:
        Sanitized string safe for PostgreSQL JSONB storage
    """
    # Remove control characters that PostgreSQL JSONB cannot handle
    # 0x09 (tab), 0x0A (newline), 0x0D (carriage return) are allowed
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", s)

    # Handle surrogate pairs and invalid UTF-8 sequences
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        # First attempt: preserve surrogates if they're part of valid pairs
        try:
            s = s.encode("utf-8", errors="surrogatepass").decode(
                "utf-8", errors="replace"
            )
        except (UnicodeDecodeError, UnicodeEncodeError):
            # Fallback: replace all problematic characters with U+FFFD
            s = s.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return s


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

    # float の NaN/Infinity は JSON 仕様で無効なため None に変換
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    # numpy の浮動小数点型も Python float に変換
    if isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)

    return obj
