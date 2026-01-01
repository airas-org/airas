from copy import deepcopy

from airas.types.research_history import ResearchHistory


def merge_history(
    old: ResearchHistory | None,
    new: ResearchHistory,
) -> ResearchHistory:
    old_dict = old.model_dump(exclude_none=True) if old else {}
    new_dict = new.model_dump(exclude_none=True)

    merged_dict = deepcopy(old_dict)
    merged_dict.update(new_dict)

    return ResearchHistory.model_validate(merged_dict)


if __name__ == "__main__":
    old_history = ResearchHistory(research_topic="valueA", queries=["valueB"])
    new_history = ResearchHistory(queries=["valueB_new"], references_bib="valueC")

    result = merge_history(old_history, new_history)
    print(f"result: {result.model_dump(exclude_none=True)}")

    # old = {"keyA": "valueA", "keyB": "valueB"}
    # new = {"keyB": "valueB_new", "keyC": "valueC"}
    # result = {"keyA": "valueA", "keyB": "valueB_new", "keyC": "valueC"}
