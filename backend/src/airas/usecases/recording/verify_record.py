from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from airas.core.research_paths import (
    COMPARISON_KEY,
    FULLTEXT_FILENAME,
    RECORD_PATH,
    RESULTS_DIR,
    SOURCES_DIR,
)
from airas.core.types.record_verification import RecordVerification
from airas.core.types.research_record import (
    AnyRun,
    ClaimDeclaration,
    ResearchRecord,
    SeyvalClaim,
    SeyvalResult,
)
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)
from airas.infra.local_git import (
    commits_with_parents,
    file_bytes_at_commit,
    is_shallow,
)
from airas.infra.run_output_store import default_store
from airas.usecases.recording._run_provenance import (
    StoreFactory,
    _ProvenanceCheckResult,
    verify_run_provenance,
)
from airas.usecases.recording.sources import quote_in
from airas.usecases.recording.update_or_load_record import (
    _ClaimStatus,
    compute_claim_statuses,
    derive_result,
    file_sha256,
    load_eval_inputs_ref,
    load_eval_report,
    load_metrics_data,
    load_provenance_manifest,
    load_record,
    runs_with_reports,
)


async def verify_record(
    local_path: str,
    *,
    check_provenance: bool = True,
    require_provenance: bool = True,
    require_history: bool = True,
    require_record: bool = True,
    store_factory: StoreFactory = default_store,
) -> RecordVerification:
    root = Path(local_path).expanduser().resolve()
    if not (root / RECORD_PATH).is_file():
        # An AIRAS repository ships record.json (empty at first), so its
        # absence is not an initial state — it was deleted, taking the
        # declarations the gate reads with it. The gate requires it;
        # verify_paper's preview (require_record=False) tolerates a paper that
        # opts out of the record system.
        problems = (
            [
                "record.json is missing: every AIRAS repository ships one "
                "(empty at first), so its absence means it was deleted"
            ]
            if require_record
            else []
        )
        return RecordVerification(ok=not problems, stage="prereg", problems=problems)

    try:
        record = load_record(str(root))
    except (ValidationError, ValueError) as e:
        return RecordVerification(
            ok=False, stage="prereg", problems=[f"{RECORD_PATH}: {e}"]
        )

    try:
        metrics_data = load_metrics_data(str(root))
    except ValueError:
        metrics_data = {}

    reported_run_ids = runs_with_reports(root, record)
    stage: Literal["prereg", "results"] = (
        "results" if metrics_data or reported_run_ids else "prereg"
    )

    problems = await asyncio.to_thread(_verify_consistency, record)
    problems += await asyncio.to_thread(_verify_literature, root, record)
    problems += await asyncio.to_thread(
        _verify_append_only, root, record, require_history
    )
    problems += await asyncio.to_thread(_verify_manifest_history, root, require_history)
    added, provenance = await _verify_additions(
        root,
        record,
        metrics_data,
        reported_run_ids,
        stage,
        check_provenance=check_provenance,
        # Turning the check off is a decision not to require it.
        require_provenance=require_provenance and check_provenance,
        store_factory=store_factory,
    )
    problems += added
    return RecordVerification(
        ok=not problems,
        stage=stage,
        problems=problems,
        provenance=provenance.model_dump() if provenance else None,
    )


# ------------------------------------------------------ the record alone
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
    return problems + _verify_pinned_once(record) + _verify_passage_references(record)


def _verify_pinned_once(record: ResearchRecord) -> list[str]:
    """A source or a passage is declared once: re-appending its id would put
    a different snapshot or quote behind the same reference."""
    problems: list[str] = []
    seen_sources: set[str] = set()
    for source in record.literature:
        if source.id in seen_sources:
            problems.append(
                f"source {source.id}: declared twice — a source is pinned once"
            )
        seen_sources.add(source.id)
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


# --------------------------------------------------------- the literature
def _verify_literature(root: Path, record: ResearchRecord) -> list[str]:
    """A source is confirmed by a registry and every passage quoted from it
    is verbatim in its snapshot — the same check whatever the source's
    origin."""
    # TODO: the agent finds papers by unconstrained web search; the record
    # shows what it read, not whether it also found test data or answers.
    problems: list[str] = []
    for source in record.active_literature():
        if not source.verified_by:
            problems.append(
                f"source {source.id}: no registry verified it (register_sources does)"
            )
        expected = f"{SOURCES_DIR}/{source.id}/{FULLTEXT_FILENAME}"
        if source.fulltext is None or source.fulltext.path != expected:
            problems.append(
                f"source {source.id}: fulltext snapshot must be {expected} "
                "(register_sources writes it)"
            )
            continue
        path = root / source.fulltext.path
        if not path.resolve().is_relative_to(root.resolve()):
            problems.append(
                f"source {source.id}: {expected} resolves outside the repository"
            )
            continue
        if not path.is_file():
            problems.append(
                f"source {source.id}: {source.fulltext.path} is missing "
                "(register_sources writes it)"
            )
            continue
        if file_sha256(path) != source.fulltext.sha256:
            problems.append(
                f"source {source.id}: {source.fulltext.path} does not match the "
                "sha256 the record holds"
            )
            continue
        fulltext = path.read_text(encoding="utf-8")
        problems += [
            f"passage {p.id}: quote is not found verbatim in {source.fulltext.path}"
            for p in source.passages
            if not quote_in(fulltext, p.quote)
        ]
    return problems


# --------------------------------------- what is already recorded
MONOTONE_KEY = "verified"

VERDICT_KEY = "verdict"

# Compared as a whole rather than key by key: a run's declared conditions
# are one declaration, and adding a condition later is as much a change as
# altering one. Letting `params` gain keys would let an empty declaration be
# filled in after the run.
LEAF_KEYS = frozenset({"params"})


def _verify_append_only(
    root: Path, record: ResearchRecord, require_history: bool
) -> list[str]:
    unavailable = (
        [
            "record.json's append-only history could not be checked (shallow "
            "clone or no git history) — CI must check out with fetch-depth: 0"
        ]
        if require_history
        else []
    )
    if is_shallow(root):
        return unavailable
    edges = commits_with_parents(root, RECORD_PATH)
    if edges is None:
        return unavailable

    # The record as of each commit involved. Absent counts as empty, so a
    # deletion is a shrink and a first creation contains nothing to lose.
    versions: dict[str, ResearchRecord] = {}
    for commit_hash in {h for commit, parents in edges for h in (commit, *parents)}:
        raw = file_bytes_at_commit(root, commit_hash, RECORD_PATH)
        if raw is None:
            versions[commit_hash] = ResearchRecord()
            continue
        try:
            versions[commit_hash] = ResearchRecord.model_validate_json(raw)
        except ValidationError:
            return [f"record.json at {commit_hash[:12]} is not a valid record"]

    # A declaration may only name passages already in the record when it
    # lands: a passage registered afterwards was not what it was grounded on.
    problems = [
        f"{commit_hash[:12]}: {problem}"
        for commit_hash, version in versions.items()
        for problem in _verify_passage_references(version)
    ]
    # Each commit against each of its parents — not against its neighbour in
    # a linear list, which would set two sibling branches against each other.
    problems += [
        f"{parent[:12]} -> {commit[:12]}: {problem}"
        for commit, parents in edges
        for parent in parents
        for problem in _containment_violations(
            versions[parent].model_dump(), versions[commit].model_dump()
        )
    ]
    head = file_bytes_at_commit(root, "HEAD", RECORD_PATH)
    committed = (
        ResearchRecord() if head is None else ResearchRecord.model_validate_json(head)
    )
    problems += [
        f"HEAD -> worktree: {problem}"
        for problem in _containment_violations(
            committed.model_dump(), record.model_dump()
        )
    ]
    return problems


def _verify_manifest_history(root: Path, require_history: bool) -> list[str]:
    """An import-time hash may not change under the same execution: once the
    backend drops the run, the hashes are all the gate has left."""
    if not (root / PROVENANCE_MANIFEST_PATH).is_file():
        return []
    unavailable = (
        [
            f"{PROVENANCE_MANIFEST_PATH}'s history could not be checked (shallow "
            "clone or no git history) — CI must check out with fetch-depth: 0"
        ]
        if require_history
        else []
    )
    if is_shallow(root):
        return unavailable
    edges = commits_with_parents(root, PROVENANCE_MANIFEST_PATH)
    if edges is None:
        return unavailable

    def manifest_at(commit_hash: str) -> RunProvenanceManifest:
        raw = file_bytes_at_commit(root, commit_hash, PROVENANCE_MANIFEST_PATH)
        try:
            return (
                RunProvenanceManifest()
                if raw is None
                else RunProvenanceManifest.model_validate_json(raw)
            )
        except ValidationError:
            return RunProvenanceManifest()

    versions = {
        h: manifest_at(h) for commit, parents in edges for h in (commit, *parents)
    }
    pairs = [
        (parent, commit, versions[parent], versions[commit])
        for commit, parents in edges
        for parent in parents
    ]
    worktree = load_provenance_manifest(root) or RunProvenanceManifest()
    pairs.append(("HEAD", "worktree", manifest_at("HEAD"), worktree))

    problems = []
    for older_hash, newer_hash, older, newer in pairs:
        for dir_name, old_entry in older.dirs.items():
            new_entry = newer.dirs.get(dir_name)
            edge = f"{older_hash[:12]} -> {newer_hash[:12]}: {PROVENANCE_MANIFEST_PATH}"
            if new_entry is None:
                problems.append(f"{edge} dropped the declaration for {dir_name}")
            elif (
                new_entry.execution_id == old_entry.execution_id
                and old_entry.files
                and new_entry.files != old_entry.files
            ):
                problems.append(
                    f"{edge} changed the import-time hashes of {dir_name} "
                    "under the same execution"
                )
    return problems


def _containment_violations(older: Any, newer: Any, path: str = "") -> list[str]:
    here = path or "(root)"

    if isinstance(older, dict) and path.rsplit(".", 1)[-1] in LEAF_KEYS:
        if older != newer:
            return [f"{here}: changed ({older!r} -> {newer!r})"]
        return []

    if isinstance(older, dict):
        if not isinstance(newer, dict):
            return [f"{here}: was an object, is now {type(newer).__name__}"]
        problems: list[str] = []
        for key, old_value in older.items():
            if key not in newer:
                problems.append(f"{here}.{key}: removed")
                continue
            child = f"{path}.{key}" if path else key
            if key == MONOTONE_KEY and old_value is False and newer[key] is True:
                continue
            if key == VERDICT_KEY and old_value is None:
                continue
            problems += _containment_violations(old_value, newer[key], child)
        return problems

    if isinstance(older, list):
        if not isinstance(newer, list):
            return [f"{here}: was a list, is now {type(newer).__name__}"]
        if len(newer) < len(older):
            return [f"{here}: entries were removed ({len(older)} -> {len(newer)})"]
        problems = []
        for index, (old_item, new_item) in enumerate(zip(older, newer, strict=False)):
            problems += _containment_violations(old_item, new_item, f"{path}[{index}]")
        return problems

    if older != newer:
        return [f"{here}: changed ({older!r} -> {newer!r})"]
    return []


# --------------------------------------- what is being appended
async def _verify_additions(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    reported_run_ids: set[str],
    stage: Literal["prereg", "results"],
    *,
    check_provenance: bool,
    require_provenance: bool,
    store_factory: StoreFactory,
) -> tuple[list[str], _ProvenanceCheckResult | None]:
    if stage == "prereg":
        # Nothing measured yet, so nothing realized may exist.
        realized = [run.run_id for run in record.run_index().values() if run.results]
        realized += [c.id for _, c in record.active_claims() if c.verified or c.verdict]
        if realized:
            return [
                "record.json holds results but no run outputs exist "
                f"({', '.join(sorted(set(realized)))})"
            ], None
        return [], None

    def _data_checks() -> list[str]:
        manifest = load_provenance_manifest(root)
        problems: list[str] = []
        for _, claim in record.active_claims():
            for _, run in claim.runs():
                if isinstance(claim, SeyvalClaim):
                    problems += _params_problems(run, manifest)
                problems += _result_problems(root, claim, run, metrics_data, manifest)
        declared_runs = set(record.run_index())
        undeclared = sorted(
            d for d in metrics_data if d != COMPARISON_KEY and d not in declared_runs
        )
        if undeclared:
            problems.append(
                "results directories no declared run accounts for: "
                + ", ".join(undeclared)
            )
        drifted = _verified_problems(
            record, compute_claim_statuses(record, reported_run_ids)
        )
        if drifted:
            problems.append(
                "claims stored as verified, or with a verdict, that the recomputation finds otherwise "
                f"({', '.join(drifted)})"
            )
        return problems

    problems = await asyncio.to_thread(_data_checks)

    provenance: _ProvenanceCheckResult | None = None
    if check_provenance:
        scope = _provenance_scope(record, metrics_data, reported_run_ids)
        if scope:
            provenance = await verify_run_provenance(str(root), scope, store_factory)

    if reported_run_ids:
        problems += _provenance_problems(provenance, require_provenance)
    return problems, provenance


def _params_problems(run: AnyRun, manifest: RunProvenanceManifest | None) -> list[str]:
    problems: list[str] = []
    declared = manifest.dirs.get(run.run_id) if manifest else None
    if declared is None or not run.params:
        return problems
    resolved = declared.parameters or {
        k.lower(): v for k, v in declared.overrides.items()
    }
    complete = bool(declared.parameters)
    for key, wanted in run.params.items():
        if key not in resolved:
            if complete:
                problems.append(
                    f"run '{run.run_id}': declared '{key}={wanted}' but "
                    "the execution resolved no such parameter"
                )
            continue
        if str(resolved[key]) != str(wanted):
            problems.append(
                f"run '{run.run_id}': declared '{key}={wanted}' but "
                f"executed '{key}={resolved[key]}'"
            )
    return problems


def _result_problems(
    root: Path,
    claim: ClaimDeclaration,
    run: AnyRun,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> list[str]:
    result = run.latest_result()
    if result is None:
        return []
    rid = run.run_id
    if not isinstance(result, SeyvalResult):
        # The verifier's report is the source; the entry must be its copy.
        expected = derive_result(root, claim, run, metrics_data, manifest)
        if expected is None or expected.model_dump() != result.model_dump():
            return [
                f"run '{rid}': the result differs from the {claim.verifier.kind} "
                "report in the results directory"
            ]
        return []

    problems: list[str] = []
    declared = manifest.dirs.get(rid) if manifest else None
    if declared is None:
        problems.append(
            f"run '{rid}': the record holds a result but no readable "
            f"{PROVENANCE_MANIFEST_PATH} entry declares an execution for "
            "this directory"
        )
    else:
        if result.id != declared.execution_id:
            problems.append(
                f"run '{rid}': the result's id {result.id!r} is not the "
                f"manifest's execution {declared.execution_id!r}"
            )
        if result.commit != declared.commit_hash:
            problems.append(
                f"run '{rid}': the result's commit {result.commit!r} is "
                f"not the manifest's {declared.commit_hash!r}"
            )

    if rid in metrics_data and result.metrics != metrics_data[rid]:
        problems.append(
            f"run '{rid}': the result's metrics differ from "
            f"{RESULTS_DIR}/{rid}/metrics.json"
        )

    expected_inputs = load_eval_inputs_ref(root, rid)
    if (result.eval_inputs is None) != (expected_inputs is None) or (
        result.eval_inputs is not None
        and expected_inputs is not None
        and result.eval_inputs.model_dump() != expected_inputs.model_dump()
    ):
        problems.append(
            f"run '{rid}': the result's eval_inputs hash does not match "
            "the eval_inputs file in the results directory"
        )

    expected_eval = load_eval_report(root, rid)
    if (result.eval_report is None) != (expected_eval is None) or (
        result.eval_report is not None
        and expected_eval is not None
        and result.eval_report.model_dump() != expected_eval.model_dump()
    ):
        problems.append(
            f"run '{rid}': the result's eval_report differs from the "
            "evaluator's report in the results directory"
        )

    # The evaluator's own `inputs_sha256` is deliberately not compared
    # with `eval_inputs.sha256`. airas-eval hashes the *parsed* payload
    # in a canonical JSON form (sorted keys, no whitespace, its own type
    # coercion), while the record hashes the file's bytes, so the two
    # digests differ for every honest run. The evaluator's digest is
    # still carried verbatim — it names what the evaluator scored in the
    # evaluator's own terms — and the file hash is what the provenance
    # step holds against the platform's stored bytes.
    return problems


def _verified_problems(
    record: ResearchRecord, statuses: list[_ClaimStatus]
) -> list[str]:
    """Claims stored as verified, or with a verdict, that the recomputation finds otherwise.

    A stored true is a fact the history must still bear out. The reverse —
    recomputed true, stored false — is not a problem: update_record has
    simply not run since the procedure completed.
    """
    recomputed = {s.id: s for s in statuses}
    drifted = []
    for _, claim in record.active_claims():
        status = recomputed.get(claim.id)
        if claim.verified and not (status and status.verified):
            drifted.append(claim.id)
        elif claim.verdict and not (status and status.verdict == claim.verdict):
            drifted.append(claim.id)
    return drifted


def _provenance_problems(
    provenance: _ProvenanceCheckResult | None, required: bool
) -> list[str]:
    # A mismatch means the local outputs are not backed by any completed run
    # in the platform's storage; "unavailable" fails only where required.
    if provenance is None:
        return (
            [
                "the provenance cross-check did not run (record.json references no results directories, or the check was disabled)"
            ]
            if required
            else []
        )
    if provenance.status == "mismatch":
        return [
            f"{provenance.source}: local outputs are not backed by stored run "
            "outputs — " + (provenance.detail or "see provenance.checks")
        ]
    if provenance.status == "unavailable" and required:
        return [
            f"provenance unavailable: {provenance.detail or 'see provenance.checks'}"
        ]
    return []


def _provenance_scope(
    record: ResearchRecord, metrics_data: dict[str, Any], reported_run_ids: set[str]
) -> set[str]:
    # Every declared run whose outputs are in: experiments by their metrics,
    # proofs and judgments by their report. All of them arrived through
    # import_run_outputs, so all of them have a store to be checked against.
    dirs = {run_id for run_id in record.run_index() if run_id in reported_run_ids}
    dirs |= {
        row.run_id
        for spec in record.active_tables()
        for row in spec.rows
        if row.run_id in metrics_data
    }
    for chart in record.active_charts():
        for ref in _metric_refs(chart.spec):
            match = max(
                (k for k in metrics_data if ref == k or ref.startswith(k + ".")),
                key=len,
                default=None,
            )
            if match:
                dirs.add(match)
    return dirs


def _metric_refs(node: Any) -> list[str]:
    if isinstance(node, str):
        return [node[len("metric:") :]] if node.startswith("metric:") else []
    if isinstance(node, dict):
        return [r for v in node.values() for r in _metric_refs(v)]
    if isinstance(node, list):
        return [r for v in node for r in _metric_refs(v)]
    return []
