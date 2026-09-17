from typing import Any

from airas.core.types.research_record import LiteratureSource, QuotedPassage


def _next_passage_id(source: LiteratureSource) -> str:
    taken = (int(p.id.rsplit(".p", 1)[1]) for p in source.passages)
    return f"{source.id}.p{max(taken, default=0) + 1}"


def add_quoted_passages(
    source: LiteratureSource, passages: list[dict[str, Any]]
) -> None:
    for passage in passages:
        if "id" in passage:
            raise ValueError("a passage id is assigned by its source, not passed in")
        source.passages.append(
            QuotedPassage.model_validate({**passage, "id": _next_passage_id(source)})
        )
