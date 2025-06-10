from copy import deepcopy
from typing import Any


def merge_history(
    old: dict[str, Any], 
    new: dict[str, Any], 
    subgraph_name: str,     
) -> dict[str, Any]:
    merged = deepcopy(old) if old else {}

    order = merged.setdefault("_order", [])
    if subgraph_name not in order:
        order.append(subgraph_name)

    merged[subgraph_name] = deepcopy(new)

    ordered = {"_order": merged["_order"]}
    for k, v in merged.items():
        if k != "_order":
            ordered[k] = v

    return ordered