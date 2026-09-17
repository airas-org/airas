from __future__ import annotations

from airas.core.types.research_record import (
    Hypothesis,
    LiteratureSource,
    ResearchRecord,
)


def find_hypothesis(record: ResearchRecord, hypothesis_id: str) -> Hypothesis:
    for hypothesis in record.hypotheses:
        if hypothesis.id == hypothesis_id:
            return hypothesis
    raise ValueError(
        f"no hypothesis '{hypothesis_id}' in the record "
        f"(have: {', '.join(h.id for h in record.hypotheses) or 'none'})"
    )


def find_source(record: ResearchRecord, source_id: str) -> LiteratureSource:
    for source in record.active_literature():
        if source.id == source_id:
            return source
    raise ValueError(
        f"no source '{source_id}' in the record "
        f"(have: {', '.join(s.id for s in record.literature) or 'none'})"
    )
