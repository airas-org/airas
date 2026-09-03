"""The check that guards the protected branch.

This gate runs on every commit, so its two failure directions are not
symmetric. A false red blocks all work in the repository — including the
commits that create the record — and a false green is a repository that
reports itself verified while contradicting its own history. Both are
covered here: the early states that must pass, and the tampering that
must not. The tampering cases follow the two checks: A, what is already
recorded (git history); B, what is being appended (the platform's record
and the files it stored).
"""

import json
import subprocess
from pathlib import Path

from airas.core.research_paths import RECORD_PATH
from airas.core.types.research_record import (
    ClaimDeclaration,
    DesignDeclaration,
    Hypothesis,
    ResearchRecord,
    RunDeclaration,
    RunResult,
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
from airas.usecases.publication.paper_values.record import load_record, save_record
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
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="The proposed method beats the baseline.",
                claims=[
                    ClaimDeclaration(
                        id="c1",
                        statement="Proposed beats baseline on accuracy.",
                        designs=[
                            DesignDeclaration(
                                id="d1",
                                summary="Head-to-head on one dataset.",
                                runs=[
                                    RunDeclaration(
                                        run_id="proposed", params={"mode": "full"}
                                    ),
                                    RunDeclaration(run_id="baseline"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )


def _c1(record: ResearchRecord) -> ClaimDeclaration:
    return record.hypotheses[0].claims[0]


def _write_results(
    repo: Path, run_commit: str, proposed_mode: str = "full"
) -> RunProvenanceManifest:
    results = repo / ".research" / "results"
    (results / "proposed").mkdir(parents=True)
    (results / "baseline").mkdir()
    (results / "proposed" / "metrics.json").write_text(json.dumps({"accuracy": 0.902}))
    (results / "baseline" / "metrics.json").write_text(json.dumps({"accuracy": 0.871}))
    manifest = RunProvenanceManifest(
        dirs={
            "proposed": ResultsDirProvenance(
                execution_id="run-a",
                commit_hash=run_commit,
                overrides={"mode": proposed_mode},
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


def _realized_repo(tmp_path: Path, proposed_mode: str = "full") -> Path:
    """A repository carried through preregistration, running and realization."""
    _init(tmp_path)
    record = _record()
    save_record(str(tmp_path), record)
    freeze = _commit(tmp_path, "prereg")

    manifest = _write_results(tmp_path, freeze, proposed_mode)
    _commit(tmp_path, "import run outputs")

    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize the record")
    return tmp_path


# --------------------------------------------------- the states that pass


def test_a_repository_with_no_record_passes(tmp_path: Path) -> None:
    """A repository that has made no claim is not contradicting one."""
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
    repo = _realized_repo(tmp_path)
    report = verify_record_only(str(repo))
    assert report.ok, report.mismatches
    assert report.stage == "results"
    assert report.append_only == "ok"
    assert report.unverified_claims == []
    assert _c1(load_record(str(repo))).verified is True


# ------------------------------------- A: what is already recorded


def test_a_reworded_claim_fails(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).statement = "Proposed is competitive with baseline."
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.append_only == "violated"


def test_a_dropped_result_fails(tmp_path: Path) -> None:
    """Deleting the run that came out badly is the failure mode."""
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).designs[0].runs[0].results.clear()
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.append_only == "violated"


def test_a_claim_declared_after_its_run_is_allowed_for_now(tmp_path: Path) -> None:
    """The order proof is not modelled yet (TODO): a claim added after its
    run executed is verified once the run's results are in."""
    _init(tmp_path)
    record = _record()
    save_record(str(tmp_path), record)
    freeze = _commit(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit(tmp_path, "import")
    record.hypotheses[0].claims.append(
        ClaimDeclaration(
            id="c2",
            statement="Post-hoc.",
            designs=[DesignDeclaration(id="d1", runs=[RunDeclaration(run_id="late")])],
        )
    )
    (tmp_path / ".research" / "results" / "late").mkdir()
    (tmp_path / ".research" / "results" / "late" / "metrics.json").write_text("{}")
    manifest.dirs["late"] = ResultsDirProvenance(
        execution_id="run-l", commit_hash=freeze
    )
    (tmp_path / PROVENANCE_MANIFEST_PATH).write_text(manifest.model_dump_json() + "\n")
    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)
    save_record(str(tmp_path), record)
    _commit(tmp_path, "post-hoc claim with results")

    report = verify_record_only(str(tmp_path))
    assert report.ok, report.mismatches
    assert report.unverified_claims == []


def test_verified_stored_true_that_the_results_no_longer_bear_out_fails(
    tmp_path: Path,
) -> None:
    """A stored true is a fact the results must still support."""
    repo = _realized_repo(tmp_path)
    # Remove a run's results: the claim's stored verified=true is now
    # contradicted by the recomputation.
    (repo / ".research" / "results" / "baseline" / "metrics.json").unlink()

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.claim_status_match is False
    assert any("stored as verified" in m for m in report.mismatches)


# ------------------------------------- B: what is being appended


def test_a_tampered_metrics_file_fails(tmp_path: Path) -> None:
    """The result's copy no longer matches the file it copied."""
    repo = _realized_repo(tmp_path)
    (repo / ".research" / "results" / "proposed" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.999})
    )
    report = verify_record_only(str(repo))
    assert not report.ok
    assert any("metrics differ" in m for m in report.mismatches)


def test_a_hand_appended_result_fails(tmp_path: Path) -> None:
    """A result naming an execution the manifest never declared."""
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).designs[0].runs[0].results.append(
        RunResult(id="run-zzz", commit="c" * 40, metrics={"accuracy": 0.999})
    )
    save_record(str(repo), record)

    report = verify_record_only(str(repo))
    assert not report.ok
    assert any("not the manifest's execution" in m for m in report.mismatches)


def test_a_result_with_no_manifest_entry_fails(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    (repo / PROVENANCE_MANIFEST_PATH).unlink()
    report = verify_record_only(str(repo))
    assert not report.ok
    assert any("no readable" in m for m in report.mismatches)


def test_a_run_dispatched_under_other_conditions_fails(tmp_path: Path) -> None:
    """Declared `mode=full`, dispatched `mode=pilot`."""
    repo = _realized_repo(tmp_path, proposed_mode="pilot")
    report = verify_record_only(str(repo))
    assert not report.ok
    assert any("executed 'mode=pilot'" in m for m in report.mismatches)


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

    (inputs_dir / "task.json").write_text(json.dumps({"predicted_labels": [0, 0]}))
    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("eval_inputs hash" in m for m in report.mismatches)


def test_an_evaluator_report_that_disagrees_with_its_inputs_fails(
    tmp_path: Path,
) -> None:
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


def test_results_no_run_declares_fail(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    undeclared = repo / ".research" / "results" / "secret-run"
    undeclared.mkdir()
    (undeclared / "metrics.json").write_text(json.dumps({"accuracy": 0.99}))

    report = verify_record_only(str(repo))
    assert not report.ok
    assert report.undeclared_result_dirs == ["secret-run"]


def test_results_in_the_record_without_run_outputs_fail(tmp_path: Path) -> None:
    _init(tmp_path)
    record = _record()
    _c1(record).designs[0].runs[0].results.append(
        RunResult(id="made-up", metrics={"accuracy": 0.99})
    )
    save_record(str(tmp_path), record)
    _commit(tmp_path, "prereg with invented results")

    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("no run outputs exist" in m for m in report.mismatches)


def test_unparseable_json_fails(tmp_path: Path) -> None:
    _init(tmp_path)
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text("{not json")
    report = verify_record_only(str(tmp_path))
    assert not report.ok
    assert any("not valid JSON" in m for m in report.mismatches)


# ------------------------------------------------------------ gate policy


def _no_seyval():
    raise RuntimeError("no Seyval credentials in this environment")


async def test_gate_passes_and_writes_its_report(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    out = repo / "record-artifact"
    summary = await run_record_gate(
        str(repo), str(out), check_provenance=False, seyval_client_factory=_no_seyval
    )
    assert summary["ok"], summary["failures"]
    assert summary["stage"] == "results"
    assert json.loads((out / RECORD_REPORT_FILENAME).read_text())["ok"] is True


async def test_gate_writes_its_report_when_red(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).statement = "softened"
    save_record(str(repo), record)
    out = repo / "record-artifact"

    summary = await run_record_gate(
        str(repo), str(out), check_provenance=False, seyval_client_factory=_no_seyval
    )
    assert not summary["ok"]
    written = json.loads((out / RECORD_REPORT_FILENAME).read_text())
    assert written["ok"] is False
    assert written["results"][0]["report"]["paper_values"]["append_only"] == "violated"


async def test_gate_does_not_demand_a_record(tmp_path: Path) -> None:
    _init(tmp_path)
    summary = await run_record_gate(
        str(tmp_path),
        str(tmp_path / "out"),
        check_provenance=False,
        seyval_client_factory=_no_seyval,
    )
    assert summary["ok"], summary["failures"]


async def test_unreachable_provenance_fails_the_gate(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
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
        r"Proposed scored \airasval{proposed.accuracy} at \airasval{proposed.params.mode}.",
        r"\end{document}",
        "",
    ]
)


def _write_paper(repo: Path) -> Path:
    latex_dir = repo / ".research" / "latex" / "mdpi"
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    record = load_record(str(repo))
    values, _ = resolve_paper_values(
        record, load_metrics_data(str(repo)), _scan_main_tex(MAIN_TEX)[1]
    )
    (latex_dir / "values.tex").write_text(render_values_tex(values, None))
    return latex_dir


async def test_a_paper_whose_numbers_match_the_record_passes(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    _write_paper(repo)
    _commit(repo, "paper")
    summary = await run_record_gate(
        str(repo), str(repo / "out"), check_provenance=False
    )
    assert summary["ok"], summary["failures"]
    assert summary["papers"] == ["mdpi"]


async def test_a_hand_edited_values_tex_is_caught_by_the_gate(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    latex_dir = _write_paper(repo)
    _commit(repo, "paper")
    values_tex = latex_dir / "values.tex"
    values_tex.write_text(values_tex.read_text().replace("0.902", "0.999"))

    summary = await run_record_gate(
        str(repo), str(repo / "out"), check_provenance=False
    )
    assert not summary["ok"]
    assert summary["results"][0]["report"]["paper_values"]["values_tex_match"] is False


async def test_a_paper_without_a_record_fails(tmp_path: Path) -> None:
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
    repo = _realized_repo(tmp_path)
    latex_dir = _write_paper(repo)
    (latex_dir / "main.tex").write_text(
        MAIN_TEX.replace(r"\airasval{proposed.accuracy}", r"\airasval{ghost.accuracy}")
    )
    _commit(repo, "paper citing a run that does not exist")

    summary = await run_record_gate(
        str(repo), str(repo / "out"), check_provenance=False
    )
    assert not summary["ok"]
    report = summary["results"][0]["report"]["paper_values"]
    assert report["undefined_keys"] == ["ghost.accuracy"]
