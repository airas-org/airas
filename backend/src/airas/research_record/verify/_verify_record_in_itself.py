"""The record's declarations, as they stand: run ids unique, criteria name their own runs, sources and passages pinned once, every named passage declared."""

from __future__ import annotations

from airas.core.research_paths import RECORD_PATH
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import ResearchRecord, SeyvalClaim, latest


def _claim_path(hypothesis_id: str, claim_id: str) -> str:
    return f"hypotheses[{hypothesis_id}]/claims[{claim_id}]"


def _verify_consistency(
    record: ResearchRecord, verification: RecordVerification
) -> None:
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
            hypothesis_id, claim_id, design_id = owner.split("/")
            verification.append_declaration_status(
                f"{_claim_path(hypothesis_id, claim_id)}/designs[{design_id}]/runs[{run.run_id}]",
                f"run '{run.run_id}' is declared under both "
                f"'{first_owner}' and '{owner}' — run ids "
                "address a results directory and must be repo-unique",
                "mismatch",
                evidence_path=RECORD_PATH,
            )

    for hypothesis, claim in record.latest_claims():
        if not claim.runs():
            verification.append_declaration_status(
                f"{_claim_path(hypothesis.id, claim.id)}/designs",
                f"claim {claim.id}: declares no run — a claim with no "
                "experiment cannot be verified",
                "mismatch",
                evidence_path=RECORD_PATH,
            )

    # Runs a criterion may compare against: only seyval runs carry metrics,
    # so a Lean or LLM-judge run could never satisfy "the same metric".
    seyval_runs = {
        run.run_id
        for _, claim in record.latest_claims()
        if isinstance(claim, SeyvalClaim)
        for _, run in claim.runs()
    }
    for hypothesis, claim in record.latest_claims():
        if not isinstance(claim, SeyvalClaim):
            continue
        criterion_path = f"{_claim_path(hypothesis.id, claim.id)}/criterion"
        own = {run.run_id for _, run in claim.runs()}
        subject = claim.criterion.subject
        verification.append_declaration_status(
            criterion_path,
            f"subject '{subject}' among this claim's runs"
            if subject in own
            else f"claim {claim.id}: criterion names run '{subject}', "
            "which this claim does not declare",
            "ok" if subject in own else "mismatch",
            evidence_path=RECORD_PATH,
        )
        # The reference may be another seyval claim's run (a shared baseline):
        # still a run of this record, and the verdict waits for its result.
        reference = claim.criterion.reference
        if isinstance(reference, str):
            verification.append_declaration_status(
                criterion_path,
                f"reference '{reference}' among the record's seyval runs"
                if reference in seyval_runs
                else f"claim {claim.id}: criterion names run '{reference}', "
                "which no seyval claim declares",
                "ok" if reference in seyval_runs else "mismatch",
                evidence_path=RECORD_PATH,
            )

    declared = set(record.run_index())
    for hypothesis in record.latest_hypotheses():
        for spec in latest(hypothesis.tables, "key"):
            for n, row in enumerate(spec.rows):
                known = row.run_id in declared or row.run_id == "comparison"
                verification.append_declaration_status(
                    f"hypotheses[{hypothesis.id}]/tables[{spec.key}]/rows[{n}]/run_id",
                    "runs the designs declare"
                    if known
                    else f"table {spec.key}: row references run '{row.run_id}', "
                    "which no design declares",
                    "ok" if known else "mismatch",
                    evidence_path=RECORD_PATH,
                )


def _verify_pinned_once(
    record: ResearchRecord, verification: RecordVerification
) -> None:
    """A source or a passage is declared once: re-appending its id would put
    a different snapshot or quote behind the same reference."""
    seen_sources: set[str] = set()
    bibkeys: dict[str, str] = {}
    for source in record.literature:
        if source.id in seen_sources:
            verification.append_declaration_status(
                f"literature[{source.id}]",
                f"source {source.id}: declared twice — a source is pinned once",
                "mismatch",
                evidence_path=RECORD_PATH,
            )
        seen_sources.add(source.id)
        if bibkeys.setdefault(source.bibkey, source.id) != source.id:
            verification.append_declaration_status(
                f"literature[{source.id}]/bibkey",
                f"source {source.id}: bibkey '{source.bibkey}' is also source "
                f"{bibkeys[source.bibkey]}'s",
                "mismatch",
                evidence_path=RECORD_PATH,
            )
        seen_passages: set[str] = set()
        for passage in source.passages:
            if passage.id in seen_passages:
                verification.append_declaration_status(
                    f"literature[{source.id}]/passages[{passage.id}]",
                    f"passage {passage.id}: declared twice — a quote is pinned once",
                    "mismatch",
                    evidence_path=RECORD_PATH,
                )
            seen_passages.add(passage.id)


def _verify_passage_references(
    record: ResearchRecord, verification: RecordVerification
) -> None:
    """Every passage a declaration names is one some source declares."""
    passages = record.passage_index()
    unknown = " '%s', which no source declares"

    def passages_named(path: str, pids: list[str], problem_head: str) -> list[str]:
        missing = [pid for pid in pids if pid not in passages]
        for pid in missing:
            verification.append_declaration_status(
                path,
                problem_head + unknown % pid,
                "mismatch",
                evidence_path=RECORD_PATH,
            )
        if pids and not missing:
            verification.append_declaration_status(
                path, "passages the sources declare", "ok", evidence_path=RECORD_PATH
            )
        return missing

    for hypothesis in record.latest_hypotheses():
        passages_named(
            f"hypotheses[{hypothesis.id}]/quoted_passage_ids",
            hypothesis.quoted_passage_ids,
            f"hypothesis {hypothesis.id}: quoted_passage_ids names passage",
        )
        for spec in latest(hypothesis.tables, "key"):
            for n, column in enumerate(spec.columns):
                if column.reference is None:
                    continue
                column_path = f"hypotheses[{hypothesis.id}]/tables[{spec.key}]/columns[{n}]/reference"
                if passages_named(
                    column_path,
                    column.reference.quoted_passage_ids,
                    f"table {spec.key}: column {column.header!r} reads passage",
                ):
                    continue
                quotes = [
                    passages[pid][1].quote
                    for pid in column.reference.quoted_passage_ids
                ]
                cited = ", ".join(column.reference.quoted_passage_ids)
                for run_id, value in column.reference.values.items():
                    stated = any(str(value) in q or f"{value:g}" in q for q in quotes)
                    verification.append_declaration_status(
                        f"{column_path}/values/{run_id}",
                        f"the quote of {cited}"
                        if stated
                        else f"table {spec.key}: column {column.header!r} gives {value!r} for "
                        f"'{run_id}', which {cited} does not state",
                        "ok" if stated else "mismatch",
                        evidence_path=RECORD_PATH,
                    )
    for hypothesis, claim in record.latest_claims():
        claim_path = _claim_path(hypothesis.id, claim.id)
        passages_named(
            f"{claim_path}/quoted_passage_ids",
            claim.quoted_passage_ids,
            f"claim {claim.id}: quoted_passage_ids names passage",
        )
        if isinstance(claim, SeyvalClaim):
            passages_named(
                f"{claim_path}/criterion",
                claim.criterion.quoted_passage_ids,
                f"claim {claim.id}: criterion names passage",
            )
        for design, _run in claim.runs():
            passages_named(
                f"{claim_path}/designs[{design.id}]/quoted_passage_ids",
                design.quoted_passage_ids,
                f"design {design.id}: quoted_passage_ids names passage",
            )


def _verify_repository_integrations(
    record: ResearchRecord, verification: RecordVerification
) -> None:
    """A design that runs a source's code names a repository of this record
    that declares the method's entry."""
    repositories = {
        repository.id: repository
        for source in record.latest_literature()
        for repository in source.repositories
    }
    for hypothesis, claim in record.latest_claims():
        if not isinstance(claim, SeyvalClaim):
            continue
        for design in latest(claim.designs, "id"):
            integration = design.repository_integration
            if integration is None:
                continue
            repository = repositories.get(integration.repository_id)
            declared = repository is not None and bool(repository.method_entry)
            verification.append_declaration_status(
                f"{_claim_path(hypothesis.id, claim.id)}/designs[{design.id}]"
                "/repository_integration/repository_id",
                "repositories of the record's sources that declare a method_entry"
                if declared
                else f"design {design.id}: repository_integration.repository_id "
                f"'{integration.repository_id}' is not a repository of this "
                "record that declares a method_entry",
                "ok" if declared else "mismatch",
                evidence_path=RECORD_PATH,
            )


def verify_record_in_itself(
    record: ResearchRecord, verification: RecordVerification
) -> None:
    _verify_consistency(record, verification)
    _verify_pinned_once(record, verification)
    _verify_passage_references(record, verification)
    _verify_repository_integrations(record, verification)
