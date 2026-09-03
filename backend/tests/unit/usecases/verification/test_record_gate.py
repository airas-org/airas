"""The check that guards the protected branch.

This gate runs on every commit, so its two failure directions are not
symmetric. A false red blocks all work in the repository — including the
commits that create the record — and a false green is a repository that
reports itself verified while contradicting its own history. Both are
covered here: the early states that must pass, and the tampering that
must not.
"""

import json
import subprocess
from pathlib import Path

import pytest

from airas.core.research_paths import RECORD_PATH
from airas.core.types.research_record import (
    Bound,
    ClaimDeclaration,
    ClaimEvaluation,
    DesignDeclaration,
    Execution,
    Hypothesis,
    ResearchRecord,
    RunDeclaration,
    Target,
)
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    ResultsDirProvenance,
    RunProvenanceManifest,
)
from airas.usecases.publication.paper_values.compute import (
    load_metrics_data,
    resolve_paper_values,
)
from airas.usecases.publication.paper_values.latex import render_values_tex
from airas.usecases.publication.paper_values.realize import realize_record
from airas.usecases.publication.paper_values.record import save_record
from airas.usecases.publication.paper_values.verify import (
    _scan_main_tex,
    paper_values_configured,
)
from airas.usecases.verification.ci_gate import (
    RECORD_REPORT_FILENAME,
    run_record_gate,
)
from airas.usecases.verification.record_gate import verify_record_only


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _init(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / "README.md").write_text("experiment repository\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _record() -> ResearchRecord:
    return ResearchRecord(
        hypothesis=Hypothesis(
            statement="The proposed method beats the baseline.",
            claims=[
                ClaimDeclaration(
                    id="c1",
                    statement="Proposed beats baseline on accuracy.",
                    target=Target(
                        op="pct_improve",
                        refs=["proposed.accuracy", "baseline.accuracy"],
                        round=1,
                    ),
                    criterion=Bound(min=0.0),
                    predicted_interval=Bound(min=2.0, max=4.0),
                    rationale="2-4 points, from the pilot",
                )
            ],
            designs=[
                DesignDeclaration(
                    id="d1",
                    summary="Head-to-head on one dataset.",
                    runs=[
                        RunDeclaration(run_id="proposed"),
                        RunDeclaration(run_id="baseline"),
                    ],
                )
            ],
        )
    )


def _write_results(repo: Path, run_commit: str) -> RunProvenanceManifest:
    results = repo / ".research" / "results"
    (results / "proposed").mkdir(parents=True)
    (results / "baseline").mkdir()
    (results / "proposed" / "metrics.json").write_text(json.dumps({"accuracy": 0.902}))
    (results / "baseline" / "metrics.json").write_text(json.dumps({"accuracy": 0.871}))
    manifest = RunProvenanceManifest(
        dirs={
            "proposed": ResultsDirProvenance(
                execution_id="run-a", commit_hash=run_commit
            ),
            "baseline": ResultsDirProvenance(
                execution_id="run-b", commit_hash=run_commit
            ),
        }
    )
    (repo / PROVENANCE_MANIFEST_PATH).write_text(
        manifest.model_dump_json(indent=2) + "\n"
    )
    return manifest


def _realized_repo(tmp_path: Path) -> tuple[Path, ResearchRecord]:
    """A repository carried through preregistration, running and realization."""
    _init(tmp_path)
    record = _record()
    save_record(str(tmp_path), record)
    freeze = _commit(tmp_path, "prereg")

    manifest = _write_results(tmp_path, freeze)
    _commit(tmp_path, "import run outputs")

    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize the record")
    return tmp_path, record


# --------------------------------------------------- the states that pass


def test_a_repository_with_no_record_passes(tmp_path: Path) -> None:
    """A repository that has made no claim is not contradicting one.

    This gate runs on every commit, so failing here would block the very
    commits that create the record.
    """
    _init(tmp_path)
    report = verify_record_only(str(tmp_path))

    assert report.ok
    assert report.stage == "prereg"
    # It must also read as not-opted-in, or the policy layer applies the
    # record-only rules (history, provenance) to a repository with none.
    assert paper_values_configured(report) is False


def test_a_preregistered_record_with_no_runs_passes(tmp_path: Path) -> None:
    _init(tmp_path)
    save_record(str(tmp_path), _record())
    _commit(tmp_path, "prereg")

    report = verify_record_only(str(tmp_path))
    assert report.ok
    assert report.stage == "prereg"
    # Declared but not yet run: unverified is the correct state, not a
    # failure — every claim starts here.
    assert report.unverified_claims == ["c1"]


def test_a_realized_record_passes(tmp_path: Path) -> None:
    repo, _ = _realized_repo(tmp_path)
    report = verify_record_only(str(repo))

    assert report.ok, report.mismatches
    assert report.stage == "results"
    assert report.append_only == "ok"
    assert report.unverified_claims == []


def test_a_verified_claim_may_miss_its_criterion(tmp_path: Path) -> None:
    """A refuted claim is a result. The gate reports it and stays green."""
    _init(tmp_path)
    record = _record()
    record.hypothesis.claims[0].criterion = Bound(min=99.0)  # unreachable
    save_record(str(tmp_path), record)
    freeze = _commit(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit(tmp_path, "import run outputs")
    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize")

    report = verify_record_only(str(tmp_path))
    assert report.ok, report.mismatches
    assert report.refuted_claims == ["c1"]
    assert report.unverified_claims == []


# ------------------------------------------------ the states that must not


def test_a_weakened_criterion_fails(tmp_path: Path) -> None:
    repo, record = _realized_repo(tmp_path)
    record.hypothesis.claims[0].criterion = Bound(min=-99.0)
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.append_only == "violated"
    assert any("criterion.min" in p for p in report.append_only_problems)


def test_a_dropped_execution_fails(tmp_path: Path) -> None:
    """Deleting the run that came out badly is the failure mode."""
    repo, record = _realized_repo(tmp_path)
    record.hypothesis.designs[0].runs[0].executions.clear()
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.append_only == "violated"


def test_a_tampered_metric_fails(tmp_path: Path) -> None:
    """The stored evaluation no longer matches a recomputation."""
    repo, _ = _realized_repo(tmp_path)
    (repo / ".research" / "results" / "proposed" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.999})
    )

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.claim_status_match is False
    assert any("claim evaluations" in m for m in report.mismatches)


def test_a_hand_written_evaluation_fails(tmp_path: Path) -> None:
    """Appending a verdict nobody computed."""
    repo, record = _realized_repo(tmp_path)
    record.hypothesis.claims[0].evaluations.append(
        ClaimEvaluation(value=42.0, display="42.0", verified=True, criterion_met=True)
    )
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.claim_status_match is False


def test_results_no_run_declares_fail(tmp_path: Path) -> None:
    """Results must not exist without a prior declaration."""
    repo, _ = _realized_repo(tmp_path)
    undeclared = repo / ".research" / "results" / "secret-run"
    undeclared.mkdir()
    (undeclared / "metrics.json").write_text(json.dumps({"accuracy": 0.99}))

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.undeclared_result_dirs == ["secret-run"]


def test_realized_results_without_run_outputs_fail(tmp_path: Path) -> None:
    """A record claiming executions in a repository that has no results."""
    _init(tmp_path)
    record = _record()
    record.hypothesis.designs[0].runs[0].executions.append(
        Execution(execution_id="made-up", metrics={"accuracy": 0.99})
    )
    save_record(str(tmp_path), record)
    _commit(tmp_path, "prereg with invented results")

    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("no run outputs exist" in m for m in report.mismatches)


def test_a_v1_record_says_which_airas_reads_it(tmp_path: Path) -> None:
    """There is no migration: containment forbids one.

    So the message has to name the cause, or this reads as a corrupt file.
    """
    _init(tmp_path)
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text(
        json.dumps({"schema_version": 1, "prereg": {"hypothesis": "H"}})
    )

    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("schema_version 1" in m for m in report.mismatches)


def test_unparseable_json_fails(tmp_path: Path) -> None:
    _init(tmp_path)
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text("{not json")

    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("not valid JSON" in m for m in report.mismatches)


def test_a_declared_override_the_run_did_not_use_fails(tmp_path: Path) -> None:
    """Declared `mode=full`, dispatched something else."""
    _init(tmp_path)
    record = _record()
    record.hypothesis.designs[0].runs[0].overrides = {"mode": "full"}
    save_record(str(tmp_path), record)
    freeze = _commit(tmp_path, "prereg")

    manifest = _write_results(tmp_path, freeze)
    manifest.dirs["proposed"].parameters = {"mode": "pilot"}
    (tmp_path / PROVENANCE_MANIFEST_PATH).write_text(
        manifest.model_dump_json(indent=2) + "\n"
    )
    _commit(tmp_path, "import run outputs")
    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize")

    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("executed 'mode=pilot'" in m for m in report.mismatches)


def test_no_git_history_is_reported_as_unavailable(tmp_path: Path) -> None:
    """Not silently ok: CI must check out with fetch-depth: 0."""
    save_record(str(tmp_path), _record())
    report = verify_record_only(str(tmp_path))
    assert report.append_only == "unavailable"


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (
            lambda r: r.hypothesis.claims[0].target.refs.__setitem__(
                0, "ghost.accuracy"
            ),
            "which no design declares",
        ),
        (
            lambda r: setattr(r.hypothesis.claims[0], "criterion", Bound()),
            "criterion is unbounded",
        ),
    ],
)
def test_declaration_problems_fail_before_any_run(
    tmp_path: Path, mutate, expected: str
) -> None:
    """Caught at freeze time, when the record can still legitimately change."""
    _init(tmp_path)
    record = _record()
    mutate(record)
    save_record(str(tmp_path), record)
    _commit(tmp_path, "prereg")

    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any(expected in m for m in report.mismatches)


# ------------------------------------------------------------ gate policy


def _no_seyval():
    raise RuntimeError("no Seyval credentials in this environment")


async def test_gate_passes_and_writes_its_report(tmp_path: Path) -> None:
    repo, _ = _realized_repo(tmp_path)
    out = repo / "record-artifact"

    summary = await run_record_gate(
        str(repo), str(out), check_provenance=False, seyval_client_factory=_no_seyval
    )

    assert summary["ok"], summary["failures"]
    assert summary["stage"] == "results"
    written = json.loads((out / RECORD_REPORT_FILENAME).read_text())
    assert written["ok"] is True


async def test_gate_writes_its_report_when_red(tmp_path: Path) -> None:
    """A red run has to be readable, or the failure is only a colour."""
    repo, record = _realized_repo(tmp_path)
    record.hypothesis.claims[0].criterion = Bound(min=-99.0)
    save_record(str(repo), record)
    out = repo / "record-artifact"

    summary = await run_record_gate(
        str(repo), str(out), check_provenance=False, seyval_client_factory=_no_seyval
    )

    assert not summary["ok"]
    assert summary["failures"]
    written = json.loads((out / RECORD_REPORT_FILENAME).read_text())
    assert written["ok"] is False
    assert any(
        "criterion.min" in p
        for p in written["results"][0]["report"]["paper_values"]["append_only_problems"]
    )


async def test_gate_does_not_demand_a_record(tmp_path: Path) -> None:
    """`require_paper_values` is off here: having a record is the paper
    gate's requirement, and this gate runs long before one exists."""
    _init(tmp_path)
    summary = await run_record_gate(
        str(tmp_path),
        str(tmp_path / "out"),
        check_provenance=False,
        seyval_client_factory=_no_seyval,
    )
    assert summary["ok"], summary["failures"]


async def test_unreachable_provenance_fails_the_gate(tmp_path: Path) -> None:
    """The byte-comparison is the strongest check in the system.

    It must not be possible to pass by making it unavailable, which is why
    CI is told never to set the allow flag.
    """
    repo, _ = _realized_repo(tmp_path)

    summary = await run_record_gate(
        str(repo),
        str(repo / "out"),
        check_provenance=True,
        seyval_client_factory=_no_seyval,
    )
    assert not summary["ok"]
    assert any("provenance" in f for f in summary["failures"])

    relaxed = await run_record_gate(
        str(repo),
        str(repo / "out2"),
        check_provenance=True,
        require_provenance=False,
        seyval_client_factory=_no_seyval,
    )
    assert relaxed["ok"], relaxed["failures"]


async def test_a_shallow_clone_fails_rather_than_passing_quietly(
    tmp_path: Path,
) -> None:
    """No history means the containment check did not run, not that it passed."""
    save_record(str(tmp_path), _record())
    summary = await run_record_gate(
        str(tmp_path),
        str(tmp_path / "out"),
        check_provenance=False,
        seyval_client_factory=_no_seyval,
    )
    assert not summary["ok"]
    assert any("fetch-depth" in f for f in summary["failures"])


# ---------------------------------------------- a paper, once one exists


MAIN_TEX = "\n".join(
    [
        r"\documentclass{article}",
        r"\input{values.tex}",
        r"\begin{document}",
        r"The gain is \airasval{c1.value}.",
        r"\end{document}",
        "",
    ]
)


def _write_paper(repo: Path, record: ResearchRecord) -> Path:
    latex_dir = repo / ".research" / "latex" / "mdpi"
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    metrics_data = load_metrics_data(str(repo))
    values, _ = resolve_paper_values(record, metrics_data, _scan_main_tex(MAIN_TEX)[1])
    (latex_dir / "values.tex").write_text(render_values_tex(values, None))
    return latex_dir


async def test_a_paper_whose_numbers_match_the_record_passes(tmp_path: Path) -> None:
    repo, record = _realized_repo(tmp_path)
    _write_paper(repo, record)
    _commit(repo, "paper")

    summary = await run_record_gate(
        str(repo), str(repo / "out"), check_provenance=False
    )
    assert summary["ok"], summary["failures"]
    assert summary["papers"] == ["mdpi"]


async def test_a_hand_edited_values_tex_is_caught_by_the_gate(tmp_path: Path) -> None:
    """The paper's numbers are integrity, not rendering.

    Caught here, before the sha can land — not at publish time, when it
    would already be on the protected branch.
    """
    repo, record = _realized_repo(tmp_path)
    latex_dir = _write_paper(repo, record)
    _commit(repo, "paper")
    values_tex = latex_dir / "values.tex"
    values_tex.write_text(values_tex.read_text().replace("3.6", "9.9"))

    summary = await run_record_gate(
        str(repo), str(repo / "out"), check_provenance=False
    )
    assert not summary["ok"]
    assert any("values.tex" in f or "ok=false" in f for f in summary["failures"])
    report = summary["results"][0]["report"]["paper_values"]
    assert report["values_tex_match"] is False


async def test_a_paper_without_a_record_fails(tmp_path: Path) -> None:
    """A repository may have no record. A paper may not: none of its
    numbers would be verifiable."""
    _init(tmp_path)
    latex_dir = tmp_path / ".research" / "latex" / "mdpi"
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    _commit(tmp_path, "paper with no record")

    summary = await run_record_gate(
        str(tmp_path), str(tmp_path / "out"), check_provenance=False
    )
    assert not summary["ok"]
    assert any("record.json is missing" in f for f in summary["failures"])


async def test_an_undeclared_airasval_key_fails(tmp_path: Path) -> None:
    repo, record = _realized_repo(tmp_path)
    latex_dir = _write_paper(repo, record)
    (latex_dir / "main.tex").write_text(
        MAIN_TEX.replace(r"\airasval{c1.value}", r"\airasval{c9.value}")
    )
    _commit(repo, "paper citing a claim that does not exist")

    summary = await run_record_gate(
        str(repo), str(repo / "out"), check_provenance=False
    )
    assert not summary["ok"]
    report = summary["results"][0]["report"]["paper_values"]
    assert report["undefined_keys"] == ["c9.value"]


# ------------------------------ the record's copies against their sources


def _reload(repo: Path) -> ResearchRecord:
    from airas.usecases.publication.paper_values.record import load_record

    return load_record(str(repo))


def test_a_hand_edited_metrics_copy_in_the_record_fails(tmp_path: Path) -> None:
    """The file is intact, so recomputation and the byte check both pass.

    Only comparing the record's copy with the file catches this.
    """
    repo, record = _realized_repo(tmp_path)
    record.hypothesis.designs[0].runs[0].executions[-1].metrics = {"accuracy": 0.999}
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert any("copy of metrics differs" in m for m in report.mismatches)


def test_an_execution_pointing_at_another_run_fails(tmp_path: Path) -> None:
    repo, record = _realized_repo(tmp_path)
    record.hypothesis.designs[0].runs[0].executions[-1].execution_id = "run-zzz"
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert any("execution_id" in m and "manifest" in m for m in report.mismatches)


def test_an_inputs_hash_that_is_not_the_file_fails(tmp_path: Path) -> None:
    _init(tmp_path)
    record = _record()
    save_record(str(tmp_path), record)
    freeze = _commit(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    inputs_dir = tmp_path / ".research" / "results" / "proposed" / "eval_inputs"
    inputs_dir.mkdir()
    (inputs_dir / "task.json").write_text(json.dumps({"predicted_labels": [1, 0]}))
    _commit(tmp_path, "import")
    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize")
    assert verify_record_only(str(tmp_path)).ok

    # The record still names the old hash; the file it hashed is gone.
    (inputs_dir / "task.json").write_text(json.dumps({"predicted_labels": [0, 0]}))
    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("inputs hash" in m for m in report.mismatches)


def test_an_evaluation_report_that_disagrees_with_its_inputs_fails(
    tmp_path: Path,
) -> None:
    """airas-eval says which inputs it computed from. The record's inputs
    hash must be that, or metrics and inputs describe two experiments."""
    _init(tmp_path)
    record = _record()
    save_record(str(tmp_path), record)
    freeze = _commit(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    run_dir = tmp_path / ".research" / "results" / "proposed"
    (run_dir / "eval_inputs").mkdir()
    (run_dir / "eval_inputs" / "task.json").write_text("{}")
    (run_dir / "evaluation").mkdir()
    (run_dir / "evaluation" / "task.json").write_text(
        json.dumps(
            {
                "task_type": "task",
                "metrics": {"accuracy": 0.902},
                "provenance": {"inputs_sha256": "f" * 64},
            }
        )
    )
    _commit(tmp_path, "import")
    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize")

    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("evaluator reports inputs" in m for m in report.mismatches)


def test_an_evaluation_attributed_to_the_wrong_execution_fails(
    tmp_path: Path,
) -> None:
    repo, record = _realized_repo(tmp_path)
    record.hypothesis.claims[0].evaluations[-1].used_executions = {
        "proposed": "run-zzz",
        "baseline": "run-b",
    }
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.claim_status_match is False
