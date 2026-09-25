"""The record's declarations, as they stand: run ids unique, criteria name their own runs, sources and passages pinned once, every named passage declared."""

from __future__ import annotations

from airas.core.types.research_record import ResearchRecord, SeyvalClaim


def _verify_consistency(record: ResearchRecord) -> list[str]:
    problems: list[str] = []

    runs_with_owner = (
        (f"{hypothesis.id}/{claim.id}/{design.id}", run)
        for hypothesis in record.hypotheses
        for claim in hypothesis.claims
        for design in claim.designs
        for run in design.runs
    )
    seen_runs: dict[str, str] = {}
    for owner, run in runs_with_owner:
        first_owner = seen_runs.setdefault(run.run_id, owner)
        if first_owner != owner:
            problems.append(
                f"run '{run.run_id}' is declared under both "
                f"'{first_owner}' and '{owner}' — run ids "
                "address a results directory and must be repo-unique"
            )

    problems += [
        f"claim {claim.id}: declares no run — a claim with no "
        "experiment cannot be verified"
        for _, claim in record.active_claims()
        if not claim.runs()
    ]

    for _, claim in record.active_claims():
        if not isinstance(claim, SeyvalClaim):
            continue
        own = {run.run_id for _, run in claim.runs()}
        named = [claim.criterion.subject]
        if isinstance(claim.criterion.reference, str):
            named.append(claim.criterion.reference)
        problems += [
            f"claim {claim.id}: criterion names run '{rid}', which this claim "
            "does not declare"
            for rid in named
            if rid not in own
        ]

    declared = set(record.run_index())
    problems += [
        f"table {spec.key}: row references run '{row.run_id}', which no design declares"
        for spec in record.active_tables()
        for row in spec.rows
        if row.run_id not in declared and row.run_id != "comparison"
    ]
    return problems


def _verify_pinned_once(record: ResearchRecord) -> list[str]:
    """A source or a passage is declared once: re-appending its id would put
    a different snapshot or quote behind the same reference."""
    problems: list[str] = []
    seen_sources: set[str] = set()
    bibkeys: dict[str, str] = {}
    for source in record.literature:
        if source.id in seen_sources:
            problems.append(
                f"source {source.id}: declared twice — a source is pinned once"
            )
        seen_sources.add(source.id)
        if bibkeys.setdefault(source.bibkey, source.id) != source.id:
            problems.append(
                f"source {source.id}: bibkey '{source.bibkey}' is also source "
                f"{bibkeys[source.bibkey]}'s"
            )
        seen_passages: set[str] = set()
        for passage in source.passages:
            if passage.id in seen_passages:
                problems.append(
                    f"passage {passage.id}: declared twice — a quote is pinned once"
                )
            seen_passages.add(passage.id)
    return problems


def _verify_passage_references(record: ResearchRecord) -> list[str]:
    """Every passage a declaration names is one some source declares."""
    known = set(record.passage_index())
    unknown = " '%s', which no source declares"
    problems: list[str] = []
    for hypothesis in record.active_hypotheses():
        problems += [
            f"hypothesis {hypothesis.id}: grounded_on names passage" + unknown % pid
            for pid in hypothesis.grounded_on
            if pid not in known
        ]
    passages = record.passage_index()
    for spec in record.active_tables():
        for column in spec.columns:
            if column.reference is None:
                continue
            if column.reference.passage not in passages:
                problems.append(
                    f"table {spec.key}: column {column.header!r} reads passage"
                    + unknown % column.reference.passage
                )
                continue
            quote = passages[column.reference.passage][1].quote
            problems += [
                f"table {spec.key}: column {column.header!r} gives {value!r} for "
                f"'{run_id}', which passage {column.reference.passage} does not state"
                for run_id, value in column.reference.values.items()
                if str(value) not in quote and f"{value:g}" not in quote
            ]
    for _, claim in record.active_claims():
        problems += [
            f"claim {claim.id}: cites_passages names passage" + unknown % pid
            for pid in claim.cites_passages
            if pid not in known
        ]
        if isinstance(claim, SeyvalClaim) and (
            ref := claim.criterion.reference_passage
        ):
            if ref not in known:
                problems.append(
                    f"claim {claim.id}: criterion's reference_passage '{ref}' is "
                    "not a passage any source declares"
                )
        for design, run in claim.runs():
            problems += [
                f"design {design.id}: cites_passages names passage" + unknown % pid
                for pid in design.cites_passages
                if pid not in known
            ]
            problems += [
                f"run '{run.run_id}': cites_passages names passage" + unknown % pid
                for pid in run.cites_passages
                if pid not in known
            ]
    return problems


def verify_record_declarations(record: ResearchRecord) -> list[str]:
    return (
        _verify_consistency(record)
        + _verify_pinned_once(record)
        + _verify_passage_references(record)
    )
