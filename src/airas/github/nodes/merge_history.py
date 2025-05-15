from copy import deepcopy
from typing import Any


def merge_history(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(old)
    for key, val in new.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = merge_history(result[key], val)
        else:
            result[key] = deepcopy(val)
    return result