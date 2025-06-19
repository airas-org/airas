from copy import deepcopy
from typing import Any


def merge_history(
    old: dict[str, Any] | None,
    new: dict[str, Any],
) -> dict[str, Any]:
    merged = deepcopy(old) if old else {}
    merged.update(new)
    return merged


if __name__ == "__main__":
    old = {"keyA": "valueA", "keyB": "valueB"}
    new = {"keyB": "valueB_new", "keyC": "valueC"}

    print(merge_history(old, new))
    # -> {'keyA': 'valueA', 'keyB': 'valueB_new', 'keyC': 'valueC'}
