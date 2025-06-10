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


if __name__ == "__main__":
    old = {
        "_order": ["Subgraph1", "Subgraph2"], 
        "Subgraph1": {"a": 1}, 
        "Subgraph2": {"x": 10, "conf": {"lr": 0.01, "epoch": 5}}
    }

    new = {
        "conf": {"epoch": 10}, "metric": 0.93
    }

    result = merge_history(
        old=old,
        new=new, 
        subgraph_name="Subgraph2"
    )
    print(f"result: {result}")