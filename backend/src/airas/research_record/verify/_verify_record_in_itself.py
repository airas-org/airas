"""The record's declarations, as they stand: run ids unique, criteria name their own runs, sources and passages pinned once, every named passage declared."""

from __future__ import annotations

from airas.core.types.research_record import ResearchRecord, SeyvalClaim, active


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

    # Runs a criterion may compare against: only seyval runs carry metrics,
    # so a Lean or LLM-judge run could never satisfy "the same metric".
    seyval_runs = {
        run.run_id
        for _, claim in record.active_claims()
        if isinstance(claim, SeyvalClaim)
        for _, run in claim.runs()
    }
    for _, claim in record.active_claims():
        if not isinstance(claim, SeyvalClaim):
            continue
        own = {run.run_id for _, run in claim.runs()}
        if claim.criterion.subject not in own:
            problems.append(
                f"claim {claim.id}: criterion names run '{claim.criterion.subject}', "
                "which this claim does not declare"
            )
        # The reference may be another seyval claim's run (a shared baseline):
        # still a run of this record, and the verdict waits for its result.
        reference = claim.criterion.reference
        if isinstance(reference, str) and reference not in seyval_runs:
            problems.append(
                f"claim {claim.id}: criterion names run '{reference}', "
                "which no seyval claim declares"
            )

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
            f"hypothesis {hypothesis.id}: quoted_passage_ids names passage"
            + unknown % pid
            for pid in hypothesis.quoted_passage_ids
            if pid not in known
        ]
    passages = record.passage_index()
    for spec in record.active_tables():
        for column in spec.columns:
            if column.reference is None:
                continue
            missing = [
                pid
                for pid in column.reference.quoted_passage_ids
                if pid not in passages
            ]
            if missing:
                problems += [
                    f"table {spec.key}: column {column.header!r} reads passage"
                    + unknown % pid
                    for pid in missing
                ]
                continue
            quotes = [
                passages[pid][1].quote for pid in column.reference.quoted_passage_ids
            ]
            cited = ", ".join(column.reference.quoted_passage_ids)
            problems += [
                f"table {spec.key}: column {column.header!r} gives {value!r} for "
                f"'{run_id}', which {cited} does not state"
                for run_id, value in column.reference.values.items()
                if not any(str(value) in q or f"{value:g}" in q for q in quotes)
            ]
    for _, claim in record.active_claims():
        problems += [
            f"claim {claim.id}: quoted_passage_ids names passage" + unknown % pid
            for pid in claim.quoted_passage_ids
            if pid not in known
        ]
        if isinstance(claim, SeyvalClaim):
            problems += [
                f"claim {claim.id}: criterion names passage" + unknown % pid
                for pid in claim.criterion.quoted_passage_ids
                if pid not in known
            ]
        for design, _run in claim.runs():
            problems += [
                f"design {design.id}: quoted_passage_ids names passage" + unknown % pid
                for pid in design.quoted_passage_ids
                if pid not in known
            ]
    return problems


def _verify_repository_integrations(record: ResearchRecord) -> list[str]:
    """A design that runs a source's code names a repository of this record
    that declares the method's entry."""
    repositories = {
        repository.id: repository
        for source in record.active_literature()
        for repository in source.repositories
    }
    problems: list[str] = []
    for _, claim in record.active_claims():
        if not isinstance(claim, SeyvalClaim):
            continue
        for design in active(claim.designs, "id"):
            integration = design.repository_integration
            if integration is None:
                continue
            repository = repositories.get(integration.repository_id)
            if repository is None or not repository.method_entry:
                problems.append(
                    f"design {design.id}: repository_integration.repository_id "
                    f"'{integration.repository_id}' is not a repository of this "
                    "record that declares a method_entry"
                )
    return problems


def verify_record_in_itself(record: ResearchRecord) -> list[str]:
    return (
        _verify_consistency(record)
        + _verify_pinned_once(record)
        + _verify_passage_references(record)
        + _verify_repository_integrations(record)
    )
