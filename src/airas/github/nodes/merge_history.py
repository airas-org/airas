from copy import deepcopy
from typing import Any


def merge_history(
    old: dict[str, Any], 
    new: dict[str, Any], 
    subgraph_name: str,     
) -> dict[str, Any]:
    merged = deepcopy(old) if old else {}

    existing_state_keys: set[str] = set()
    for name, subdict in merged.items():
        if name != "_order" and isinstance(subdict, dict):
            existing_state_keys.update(subdict.keys())

    delta = {k: v for k, v in new.items() if k not in existing_state_keys}
    if not delta:
        return merged              

    order = merged.setdefault("_order", [])
    if subgraph_name not in order:
        order.append(subgraph_name)

    merged.setdefault(subgraph_name, {}).update(delta)

    ordered = {"_order": order}
    for name in order:
        if name in merged:
            ordered[name] = merged[name]

    return ordered

if __name__ == "__main__":
    old_1 = {
        "_order": ["Subgraph_A", "Subgraph_B"],
        "Subgraph_A": {"keyA": "valueA"},
        "Subgraph_B": {"keyB": "valueB"},
    }
    new_1 = {"keyA": "valueA", "keyB": "valueB", "keyC": "valueC"}

    result_1 = merge_history(old_1, new_1, "Subgraph_C")
    print(result_1)
