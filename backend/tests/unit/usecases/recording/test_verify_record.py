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

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

from airas.core.research_paths import RECORD_PATH
from airas.core.types.research_record import (
    ClaimDeclaration,
    Hypothesis,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalResult,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    ResultsDirProvenance,
    RunProvenanceManifest,
)
from airas.usecases.publication.map_record_to_publication import (
    render_values_tex,
    resolve_paper_values,
)
from airas.usecases.publication.verify_paper import scan_main_tex, verify_paper
from airas.usecases.recording.update_or_load_record import (
    load_metrics_data,
    load_record,
    save_record,
    update_record_with_results,
)
from airas.usecases.recording.verify_record import RecordVerification, verify_record

SEYVAL = SeyvalVerifier(kind=VerifierKind.SEYVAL)


def _verify(path: str, **kw: Any) -> RecordVerification:
    # The record's own checks; CI policy (history, provenance) is opted into per test.
    kw.setdefault("check_provenance", False)
    kw.setdefault("require_history", False)
    return asyncio.run(verify_record(path, **kw))


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
                    SeyvalClaim(
                        verifier=SEYVAL,
                        id="c1",
                        statement="Proposed beats baseline on accuracy.",
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                summary="Head-to-head on one dataset.",
                                runs=[
                                    SeyvalRun(
                                        run_id="proposed", params={"mode": "full"}
                                    ),
                                    SeyvalRun(run_id="baseline"),
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

    update_record_with_results(
        tmp_path, record, load_metrics_data(str(tmp_path)), manifest
    )
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize the record")
    return tmp_path


# --------------------------------------------------- the states that pass


def test_a_repository_with_no_record_passes(tmp_path: Path) -> None:
    """A repository that has made no claim is not contradicting one."""
    _init(tmp_path)
    report = _verify(str(tmp_path))
    assert report.ok
    assert report.stage == "prereg"
    assert report.problems == []


def test_a_preregistered_record_with_no_runs_passes(tmp_path: Path) -> None:
    _init(tmp_path)
    save_record(str(tmp_path), _record())
    _commit(tmp_path, "prereg")

    report = _verify(str(tmp_path))
    assert report.ok
    assert report.stage == "prereg"
    # Declared but not yet run: unverified is the correct state, not a
    # failure — every claim starts here.
    assert report.problems == []


def test_a_realized_record_passes(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    report = _verify(str(repo))
    assert report.ok, report.problems
    assert report.stage == "results"
    assert report.problems == []
    assert _c1(load_record(str(repo))).verified is True


# ------------------------------------- A: what is already recorded


def test_a_reworded_claim_fails(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).statement = "Proposed is competitive with baseline."
    save_record(str(repo), record)

    report = _verify(str(repo))
    assert not report.ok
    assert any("statement" in p for p in report.problems)


def test_a_dropped_result_fails(tmp_path: Path) -> None:
    """Deleting the run that came out badly is the failure mode."""
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).designs[0].runs[0].results.clear()
    save_record(str(repo), record)

    report = _verify(str(repo))
    assert not report.ok
    assert any("removed" in p for p in report.problems)


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
        SeyvalClaim(
            verifier=SEYVAL,
            id="c2",
            statement="Post-hoc.",
            designs=[SeyvalDesign(id="d1", runs=[SeyvalRun(run_id="late")])],
        )
    )
    (tmp_path / ".research" / "results" / "late").mkdir()
    (tmp_path / ".research" / "results" / "late" / "metrics.json").write_text("{}")
    manifest.dirs["late"] = ResultsDirProvenance(
        execution_id="run-l", commit_hash=freeze
    )
    (tmp_path / PROVENANCE_MANIFEST_PATH).write_text(manifest.model_dump_json() + "\n")
    update_record_with_results(
        tmp_path, record, load_metrics_data(str(tmp_path)), manifest
    )
    save_record(str(tmp_path), record)
    _commit(tmp_path, "post-hoc claim with results")

    report = _verify(str(tmp_path))
    assert report.ok, report.problems


def test_verified_stored_true_that_the_results_no_longer_bear_out_fails(
    tmp_path: Path,
) -> None:
    """A stored true is a fact the results must still support."""
    repo = _realized_repo(tmp_path)
    # Remove a run's results: the claim's stored verified=true is now
    # contradicted by the recomputation.
    (repo / ".research" / "results" / "baseline" / "metrics.json").unlink()

    report = _verify(str(repo))
    assert not report.ok
    assert any("stored as verified" in m for m in report.problems)


# ------------------------------------- B: what is being appended


def test_a_tampered_metrics_file_fails(tmp_path: Path) -> None:
    """The result's copy no longer matches the file it copied."""
    repo = _realized_repo(tmp_path)
    (repo / ".research" / "results" / "proposed" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.999})
    )
    report = _verify(str(repo))
    assert not report.ok
    assert any("metrics differ" in m for m in report.problems)


def test_a_hand_appended_result_fails(tmp_path: Path) -> None:
    """A result naming an execution the manifest never declared."""
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).designs[0].runs[0].results.append(
        SeyvalResult(
            verifier="seyval",
            id="run-zzz",
            commit="c" * 40,
            metrics={"accuracy": 0.999},
        )
    )
    save_record(str(repo), record)

    report = _verify(str(repo))
    assert not report.ok
    assert any("not the manifest's execution" in m for m in report.problems)


def test_a_result_with_no_manifest_entry_fails(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    (repo / PROVENANCE_MANIFEST_PATH).unlink()
    report = _verify(str(repo))
    assert not report.ok
    assert any("no readable" in m for m in report.problems)


def test_a_run_dispatched_under_other_conditions_fails(tmp_path: Path) -> None:
    """Declared `mode=full`, dispatched `mode=pilot`."""
    repo = _realized_repo(tmp_path, proposed_mode="pilot")
    report = _verify(str(repo))
    assert not report.ok
    assert any("executed 'mode=pilot'" in m for m in report.problems)


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
    update_record_with_results(
        tmp_path, record, load_metrics_data(str(tmp_path)), manifest
    )
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize")
    assert _verify(str(tmp_path)).ok

    (inputs_dir / "task.json").write_text(json.dumps({"predicted_labels": [0, 0]}))
    report = _verify(str(tmp_path))
    assert not report.ok
    assert any("eval_inputs hash" in m for m in report.problems)


def test_the_evaluators_own_inputs_digest_is_not_held_against_the_file_hash(
    tmp_path: Path,
) -> None:
    """airas-eval hashes the canonical parsed payload, the record the bytes.

    The two digests never agree, even for an honest run, so comparing them
    would fail every repository. The evaluator's digest is recorded as-is.
    """
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
    update_record_with_results(
        tmp_path, record, load_metrics_data(str(tmp_path)), manifest
    )
    save_record(str(tmp_path), record)
    _commit(tmp_path, "realize")

    report = _verify(str(tmp_path))
    assert report.ok, report.problems
    run = record.hypotheses[0].claims[0].designs[0].runs[0]
    assert run.results[-1].eval_report is not None
    assert run.results[-1].eval_report.inputs_sha256 == "f" * 64


def test_results_no_run_declares_fail(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    undeclared = repo / ".research" / "results" / "secret-run"
    undeclared.mkdir()
    (undeclared / "metrics.json").write_text(json.dumps({"accuracy": 0.99}))

    report = _verify(str(repo))
    assert not report.ok
    assert any("secret-run" in m for m in report.problems)


def test_results_in_the_record_without_run_outputs_fail(tmp_path: Path) -> None:
    _init(tmp_path)
    record = _record()
    _c1(record).designs[0].runs[0].results.append(
        SeyvalResult(verifier="seyval", id="made-up", metrics={"accuracy": 0.99})
    )
    save_record(str(tmp_path), record)
    _commit(tmp_path, "prereg with invented results")

    report = _verify(str(tmp_path))
    assert not report.ok
    assert any("no run outputs exist" in m for m in report.problems)


def test_unparseable_json_fails(tmp_path: Path) -> None:
    _init(tmp_path)
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text("{not json")
    report = _verify(str(tmp_path))
    assert not report.ok
    assert any("Invalid JSON" in m for m in report.problems)


# ------------------------------------------------------------ CI policy


def _no_seyval():
    raise RuntimeError("no Seyval credentials in this environment")


def test_a_realized_record_passes_with_history_required(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    result = _verify(str(repo), require_history=True, seyval_client_factory=_no_seyval)
    assert result.ok, result.problems
    assert result.stage == "results"


def test_a_reworded_claim_is_reported_as_violated_history(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).statement = "softened"
    save_record(str(repo), record)
    result = _verify(str(repo), require_history=True)
    assert not result.ok
    assert any("statement" in p for p in result.problems)


def test_a_repository_without_a_record_is_not_demanded_one(tmp_path: Path) -> None:
    _init(tmp_path)
    result = _verify(
        str(tmp_path), require_history=True, seyval_client_factory=_no_seyval
    )
    assert result.ok
    assert result.stage == "prereg"


def test_unreachable_provenance_fails_where_required(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    result = _verify(str(repo), check_provenance=True, seyval_client_factory=_no_seyval)
    assert not result.ok
    assert any("provenance" in p for p in result.problems)

    relaxed = _verify(
        str(repo),
        check_provenance=True,
        require_provenance=False,
        seyval_client_factory=_no_seyval,
    )
    assert relaxed.ok, relaxed.problems


def test_a_shallow_clone_fails_rather_than_passing_quietly(tmp_path: Path) -> None:
    save_record(str(tmp_path), _record())
    result = _verify(str(tmp_path), require_history=True)
    assert not result.ok
    assert any("fetch-depth" in p for p in result.problems)


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
        record, load_metrics_data(str(repo)), scan_main_tex(MAIN_TEX)[1]
    )
    (latex_dir / "values.tex").write_text(render_values_tex(values, None))
    return latex_dir


def _verify_paper(path: str, **kw: Any):
    kw.setdefault("check_provenance", False)
    kw.setdefault("require_history", False)
    return asyncio.run(verify_paper(path, "mdpi", **kw))


def test_a_paper_whose_numbers_match_the_record_passes(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    _write_paper(repo)
    _commit(repo, "paper")
    result = _verify_paper(str(repo))
    assert result.ok, result.record.problems + result.problems


def test_a_hand_edited_values_tex_is_caught(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    latex_dir = _write_paper(repo)
    _commit(repo, "paper")
    values_tex = latex_dir / "values.tex"
    values_tex.write_text(values_tex.read_text().replace("0.902", "0.999"))

    result = _verify_paper(str(repo))
    assert not result.ok
    assert any("differs from its regeneration" in p for p in result.problems)


def test_a_paper_without_a_record_fails(tmp_path: Path) -> None:
    _init(tmp_path)
    latex_dir = tmp_path / ".research" / "latex" / "mdpi"
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    _commit(tmp_path, "paper with no record")

    result = _verify_paper(str(tmp_path))
    assert not result.ok
    assert any("record.json is missing" in p for p in result.problems)
    assert _verify_paper(str(tmp_path), require_record=False).ok


def test_an_undeclared_airasval_key_fails(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    latex_dir = _write_paper(repo)
    (latex_dir / "main.tex").write_text(
        MAIN_TEX.replace(r"\airasval{proposed.accuracy}", r"\airasval{ghost.accuracy}")
    )
    _commit(repo, "paper citing a run that does not exist")

    result = _verify_paper(str(repo))
    assert not result.ok
    assert any("ghost.accuracy" in p for p in result.problems)
