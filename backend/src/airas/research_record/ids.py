"""Allocating the next source and passage id in the record."""

from __future__ import annotations

from airas.core.types.research_record import LiteratureSource, ResearchRecord


def next_source_id(record: ResearchRecord) -> str:
    return f"s{max((int(s.id[1:]) for s in record.literature), default=0) + 1}"


def next_passage_id(source: LiteratureSource) -> str:
    taken = (int(p.id.rsplit(".p", 1)[1]) for p in source.passages)
    return f"{source.id}.p{max(taken, default=0) + 1}"
