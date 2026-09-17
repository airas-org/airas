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

from airas.core.research_paths import RECORD_PATH, RESULTS_DIR
from airas.core.types.research_record import (
    ClaimDeclaration,
    Criterion,
    Hypothesis,
    LiteratureSource,
    Prediction,
    QuotedPassage,
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
from airas.research_record.read.load_record import load_record
from airas.research_record.read.read_run_outputs import load_metrics_data
from airas.research_record.read.scan_main_tex import scan_main_tex
from airas.research_record.render.render_claims_tex import render_claims_tex
from airas.research_record.render.render_paper_values import (
    render_values_tex,
    resolve_paper_values,
)
from airas.research_record.render.render_references_bib import render_references_bib
from airas.research_record.update._add_literatures import (
    _write_fulltext as write_fulltext,
)
from airas.research_record.update.append_to_record import (
    _append_run_results as update_record_with_results,
)
from airas.research_record.verify._verify_citation_meaning import (
    _collect_citations as collect_citations,
)
from airas.research_record.verify.verify_paper import verify_paper
from airas.research_record.verify.verify_record import RecordVerification, verify_record

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
                        rationale="Head-to-head on the hypothesis's own metric.",
                        criterion=Criterion(
                            metric="accuracy",
                            subject="proposed",
                            reference="baseline",
                            op=">=",
                            margin=0.02,
                        ),
                        prediction=Prediction(low=0.02, high=0.04, basis="pilot"),
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
    record.save(str(tmp_path))
    freeze = _commit(tmp_path, "prereg")

    manifest = _write_results(tmp_path, freeze, proposed_mode)
    _commit(tmp_path, "import run outputs")

    update_record_with_results(
        tmp_path, record, load_metrics_data(str(tmp_path)), manifest
    )
    record.save(str(tmp_path))
    _commit(tmp_path, "realize the record")
    return tmp_path


# --------------------------------------------------- the states that pass


def test_a_repository_with_no_record_fails(tmp_path: Path) -> None:
    """record.json is mandatory: every repository ships one, so its absence is a deletion."""
    _init(tmp_path)
    report = _verify(str(tmp_path))
    assert not report.ok
    assert any("record.json is missing" in p for p in report.problems)


def test_a_preregistered_record_with_no_runs_passes(tmp_path: Path) -> None:
    _init(tmp_path)
    _record().save(str(tmp_path))
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
    record.save(str(repo))

    report = _verify(str(repo))
    assert not report.ok
    assert any("statement" in p for p in report.problems)


def test_a_dropped_result_fails(tmp_path: Path) -> None:
    """Deleting the run that came out badly is the failure mode."""
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).designs[0].runs[0].results.clear()
    record.save(str(repo))

    report = _verify(str(repo))
    assert not report.ok
    assert any("removed" in p for p in report.problems)


def test_a_claim_declared_after_its_run_is_allowed_for_now(tmp_path: Path) -> None:
    """The order proof is not modelled yet (TODO): a claim added after its
    run executed is verified once the run's results are in."""
    _init(tmp_path)
    record = _record()
    record.save(str(tmp_path))
    freeze = _commit(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    _commit(tmp_path, "import")
    record.hypotheses[0].claims.append(
        SeyvalClaim(
            verifier=SEYVAL,
            id="c2",
            statement="Post-hoc.",
            rationale="Head-to-head on the hypothesis's own metric.",
            criterion=Criterion(
                metric="accuracy", subject="late", reference=0.5, op=">="
            ),
            prediction=Prediction(low=0.1, high=0.3, basis="pilot"),
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
    record.save(str(tmp_path))
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
    record.save(str(repo))

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
    record.save(str(tmp_path))
    freeze = _commit(tmp_path, "prereg")
    manifest = _write_results(tmp_path, freeze)
    inputs_dir = tmp_path / ".research" / "results" / "proposed" / "eval_inputs"
    inputs_dir.mkdir()
    (inputs_dir / "task.json").write_text(json.dumps({"predicted_labels": [1, 0]}))
    _commit(tmp_path, "import")
    update_record_with_results(
        tmp_path, record, load_metrics_data(str(tmp_path)), manifest
    )
    record.save(str(tmp_path))
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
    record.save(str(tmp_path))
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
    record.save(str(tmp_path))
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
    record.save(str(tmp_path))
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


def _no_store(backend: str, git_url: str):
    raise RuntimeError("no backend credentials in this environment")


def test_a_realized_record_passes_with_history_required(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    result = _verify(str(repo), require_history=True, store_factory=_no_store)
    assert result.ok, result.problems
    assert result.stage == "results"


def test_a_reworded_claim_is_reported_as_violated_history(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    _c1(record).statement = "softened"
    record.save(str(repo))
    result = _verify(str(repo), require_history=True)
    assert not result.ok
    assert any("statement" in p for p in result.problems)


def test_a_missing_record_is_tolerated_when_not_required(tmp_path: Path) -> None:
    # The escape hatch for a paper that opts out of the record system.
    _init(tmp_path)
    result = _verify(str(tmp_path), require_record=False)
    assert result.ok
    assert result.stage == "prereg"


def test_unreachable_provenance_fails_where_required(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    result = _verify(str(repo), check_provenance=True, store_factory=_no_store)
    assert not result.ok
    assert any("provenance" in p for p in result.problems)

    relaxed = _verify(
        str(repo),
        check_provenance=True,
        require_provenance=False,
        store_factory=_no_store,
    )
    assert relaxed.ok, relaxed.problems
    # What the cross-check found travels with the result, so CI's report can
    # show it (status, sibling runs) rather than only a pass/fail.
    assert relaxed.provenance is not None
    assert relaxed.provenance["status"] == "unavailable"


def test_a_shallow_clone_fails_rather_than_passing_quietly(tmp_path: Path) -> None:
    _record().save(str(tmp_path))
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
    (latex_dir / "claims.tex").write_text(
        render_claims_tex(record, load_metrics_data(str(repo)))
    )
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


# ------------------------------------------------- the claim's criterion


def test_the_criterion_decides_the_verdict(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    claim = _c1(load_record(str(repo)))
    assert claim.verified and claim.verdict == "supported"  # 0.902 - 0.871 >= 0.02
    assert _verify(str(repo)).ok


def test_a_rerun_that_flips_the_outcome_is_drift_not_a_new_verdict(
    tmp_path: Path,
) -> None:
    repo = _realized_repo(tmp_path)
    record = load_record(str(repo))
    (repo / ".research" / "results" / "proposed" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.875})
    )
    manifest = RunProvenanceManifest(
        dirs={
            "proposed": ResultsDirProvenance(
                execution_id="run-a2", commit_hash=_git(repo, "rev-parse", "HEAD")
            ),
            "baseline": ResultsDirProvenance(execution_id="run-b"),
        }
    )
    (repo / PROVENANCE_MANIFEST_PATH).write_text(manifest.model_dump_json())
    statuses, _ = update_record_with_results(
        repo, record, load_metrics_data(str(repo)), manifest
    )
    assert statuses[0].verdict == "refuted"
    assert _c1(record).verdict == "supported"  # written once, never back
    record.save(str(repo))
    _commit(repo, "re-run")

    result = _verify(str(repo))
    assert not result.ok
    assert any("with a verdict" in p for p in result.problems)


def test_a_paper_may_list_its_claims_before_any_run(tmp_path: Path) -> None:
    _init(tmp_path)
    record = _record()
    record.save(str(tmp_path))
    latex_dir = tmp_path / ".research" / "latex" / "mdpi"
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(
        MAIN_TEX.replace(r"\input{values.tex}", r"\input{claims.tex}")
    )
    (latex_dir / "claims.tex").write_text(render_claims_tex(record, {}))
    _commit(tmp_path, "prereg")

    result = _verify_paper(str(tmp_path))
    assert result.ok, result.record.problems + result.problems
    assert result.record.stage == "prereg"
    assert "pending" in (latex_dir / "claims.tex").read_text()


def test_a_missing_or_hand_edited_claims_tex_is_caught(tmp_path: Path) -> None:
    repo = _realized_repo(tmp_path)
    latex_dir = _write_paper(repo)
    _commit(repo, "paper")
    claims_tex = latex_dir / "claims.tex"
    claims_tex.write_text(claims_tex.read_text().replace("supported", "refuted"))
    result = _verify_paper(str(repo))
    assert any("claims.tex differs" in p for p in result.problems)

    claims_tex.unlink()
    result = _verify_paper(str(repo))
    assert any("claims.tex is missing" in p for p in result.problems)


def test_an_empty_record_verifies(tmp_path: Path) -> None:
    # The state every repository ships in: record.json present but empty.
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text("{}")
    _init(tmp_path)

    result = _verify(str(tmp_path))
    assert result.ok


def test_deleting_the_record_after_declaring_it_fails(tmp_path: Path) -> None:
    _init(tmp_path)
    _record().save(str(tmp_path))
    _commit(tmp_path, "preregister")
    (tmp_path / RECORD_PATH).unlink()
    _commit(tmp_path, "delete the record")

    result = _verify(str(tmp_path))
    assert not result.ok
    assert any("record.json is missing" in p for p in result.problems)


def test_a_merge_cannot_hide_a_landed_declaration(tmp_path: Path) -> None:
    # git merge -s ours makes the protected tip an ancestor while keeping the
    # rewritten record; git's simplified path walk never listed that tip.
    _init(tmp_path)
    ResearchRecord().save(str(tmp_path))
    base = _commit(tmp_path, "initial empty record")
    _record().save(str(tmp_path))
    _commit(tmp_path, "frozen original claim")
    _git(tmp_path, "branch", "protected-main")
    _git(tmp_path, "checkout", "-qb", "side", base)
    modified = _record()
    modified.hypotheses[0].claims[0].statement = "CHANGED AFTER FREEZE"
    modified.save(str(tmp_path))
    _commit(tmp_path, "rewrite claim on side")
    _git(tmp_path, "merge", "-s", "ours", "--no-edit", "protected-main")

    result = _verify(str(tmp_path))
    assert not result.ok
    assert any("statement" in p for p in result.problems)


def _record_with(claim_ids: list[str]) -> ResearchRecord:
    # One hypothesis with the given claims, run ids unique across claims.
    return ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="The proposed method beats the baseline.",
                claims=[
                    SeyvalClaim(
                        verifier=SEYVAL,
                        id=cid,
                        statement=f"{cid}: proposed beats baseline.",
                        rationale="Head-to-head on the hypothesis's own metric.",
                        criterion=Criterion(
                            metric="accuracy",
                            subject=f"{cid}-proposed",
                            reference=f"{cid}-baseline",
                            op=">=",
                            margin=0.02,
                        ),
                        prediction=Prediction(low=0.02, high=0.04, basis="pilot"),
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                summary="Head-to-head on one dataset.",
                                runs=[
                                    SeyvalRun(run_id=f"{cid}-proposed"),
                                    SeyvalRun(run_id=f"{cid}-baseline"),
                                ],
                            )
                        ],
                    )
                    for cid in claim_ids
                ],
            )
        ]
    )


def _fork(tmp_path: Path) -> str:
    """c1 on the base; `trunk` appends c2; `side` branches from the base."""
    _init(tmp_path)
    _record_with(["c1"]).save(str(tmp_path))
    base = _commit(tmp_path, "c1")
    _git(tmp_path, "branch", "trunk")
    _git(tmp_path, "checkout", "-q", "trunk")
    _record_with(["c1", "c2"]).save(str(tmp_path))
    _commit(tmp_path, "trunk appends c2")
    _git(tmp_path, "checkout", "-qb", "side", base)
    return base


def test_merging_main_into_a_branch_that_did_not_touch_the_record_passes(
    tmp_path: Path,
) -> None:
    """The realistic update-merge: main appended a claim, the branch only
    changed code. The merge equals main's record and extends the branch's."""
    _fork(tmp_path)
    (tmp_path / "README.md").write_text("code only\n")
    _commit(tmp_path, "side: code only")
    _git(tmp_path, "merge", "--no-edit", "trunk")

    result = _verify(str(tmp_path))
    assert result.ok, result.problems


def test_a_merge_of_two_concurrent_appends_is_an_append_only_conflict(
    tmp_path: Path,
) -> None:
    """Append-only lists grow at the end: every revision keeps the prior one
    as a prefix (reordering fails too). Two branches that each append a
    claim cannot both be prefixes of one merge, so the merge fails against
    one parent. Declarations are serialised — the fast-forward-only flow
    never produces this — and such a merge must be redone as a linear
    append."""
    _fork(tmp_path)
    _record_with(["c1", "c3"]).save(str(tmp_path))
    _commit(tmp_path, "side appends c3")
    subprocess.run(  # conflicts on record.json; resolved below as the union
        ["git", "-C", str(tmp_path), "merge", "--no-commit", "--no-edit", "trunk"],
        capture_output=True,
    )
    _record_with(["c1", "c2", "c3"]).save(str(tmp_path))
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "merge: union of both appends")

    result = _verify(str(tmp_path))
    assert not result.ok
    assert any("changed" in p for p in result.problems)


# ------------------------------------------ the provenance manifest's history


def test_import_time_hashes_may_not_change_under_the_same_execution(
    tmp_path: Path,
) -> None:
    repo = _realized_repo(tmp_path)
    manifest_path = repo / PROVENANCE_MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text())
    entry = manifest["dirs"]["proposed"]
    entry["files"] = {f"{RESULTS_DIR}/proposed/metrics.json": "0" * 64}
    manifest_path.write_text(json.dumps(manifest))
    _commit(repo, "import with hashes")

    # A new execution may replace the entry wholesale.
    entry["execution_id"] = "another-run"
    entry["files"] = {f"{RESULTS_DIR}/proposed/metrics.json": "1" * 64}
    manifest_path.write_text(json.dumps(manifest))
    _commit(repo, "re-import from another run")
    result = _verify(str(repo), require_history=True)
    assert not any(PROVENANCE_MANIFEST_PATH in p for p in result.problems), (
        result.problems
    )

    # The same execution may not: the hashes are what outlives the store.
    entry["files"] = {f"{RESULTS_DIR}/proposed/metrics.json": "2" * 64}
    manifest_path.write_text(json.dumps(manifest))
    result = _verify(str(repo), require_history=True)
    assert any("import-time hashes" in p for p in result.problems), result.problems

    # Nor may a declaration be dropped.
    del manifest["dirs"]["proposed"]
    manifest_path.write_text(json.dumps(manifest))
    result = _verify(str(repo), require_history=True)
    assert any("dropped the declaration" in p for p in result.problems), result.problems


# ------------------------------------------------------------ the literature


PAGES = [
    "Attention Is All You Need\nWe propose the Transformer.",
    "We apply dropout to the output of each sub-layer.\nThe rate is 0.1.",
]
QUOTE = "We apply dropout to the output of each sub-layer."


def find_source(repo: Path, confirmed: bool = True) -> LiteratureSource:
    return LiteratureSource(
        id="s1",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani"],
        year=2017,
        bibkey="vaswani-2017-attention",
        verified_by="airas_db" if confirmed else "",
        verified_at="2026-09-15T00:00:00+00:00",
        fulltext=write_fulltext(repo, "s1", PAGES),
        parser="pymupdf test",
        passages=[QuotedPassage(id="s1.p1", node_type="method", quote=QUOTE)],
    )


def _grounded_repo(tmp_path: Path, **source_kw: Any) -> tuple[Path, ResearchRecord]:
    _init(tmp_path)
    record = _record()
    record.literature.append(find_source(tmp_path, **source_kw))
    record.hypotheses[0].grounded_on = ["s1.p1"]
    _c1(record).cites_passages = ["s1.p1"]
    record.save(str(tmp_path))
    return tmp_path, record


def test_a_hypothesis_grounded_on_a_registered_passage_passes(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _commit(repo, "prereg")
    result = _verify(str(repo))
    assert result.ok, result.problems


def test_grounds_naming_a_passage_no_source_declares_fail(tmp_path: Path) -> None:
    repo, record = _grounded_repo(tmp_path)
    record.hypotheses[0].grounded_on.append("s1.p9")
    record.save(str(repo))
    result = _verify(str(repo))
    assert any("hypothesis h1" in p and "'s1.p9'" in p for p in result.problems)


def test_a_quote_not_in_the_snapshot_fails(tmp_path: Path) -> None:
    repo, record = _grounded_repo(tmp_path)
    record.literature[0].passages[0].quote = "Dropout of 0.1 is applied."
    record.save(str(repo))
    result = _verify(str(repo))
    assert any("passage s1.p1" in p and "verbatim" in p for p in result.problems)


def test_a_snapshot_edited_after_registration_fails(tmp_path: Path) -> None:
    repo, record = _grounded_repo(tmp_path)
    path = repo / record.literature[0].fulltext.path
    path.write_text(path.read_text() + " ")
    result = _verify(str(repo))
    assert any("sha256" in p for p in result.problems)


def test_a_source_no_registry_verified_fails(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path, confirmed=False)
    result = _verify(str(repo))
    assert any("no registry verified it" in p for p in result.problems)


def test_a_passage_registered_after_the_hypothesis_that_names_it_fails(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    record = ResearchRecord(literature=[find_source(tmp_path)])
    record.literature[0].passages.clear()
    record.save(str(tmp_path))
    _commit(tmp_path, "register the source")

    record.hypotheses = _record().hypotheses
    record.hypotheses[0].grounded_on = ["s1.p1"]
    record.save(str(tmp_path))
    grounded = _commit(tmp_path, "prereg naming a passage that is not there yet")

    record.literature[0].passages.append(
        QuotedPassage(id="s1.p1", node_type="method", quote=QUOTE)
    )
    record.save(str(tmp_path))
    _commit(tmp_path, "the passage, after the fact")

    # The worktree alone is consistent; the history is what convicts it.
    result = _verify(str(tmp_path))
    assert not result.ok
    assert all(p.startswith(grounded[:12]) for p in result.problems), result.problems
    assert any("s1.p1" in p for p in result.problems)


# ------------------------------------------ a paper that cites the literature


def _write_cited_paper(repo: Path, body: str, bib: str | None = None) -> None:
    latex_dir = repo / ".research" / "latex" / "mdpi"
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(
        "\\documentclass{article}\n\\begin{document}\n" + body + "\n\\end{document}\n"
    )
    record = load_record(str(repo))
    (latex_dir / "claims.tex").write_text(render_claims_tex(record, {}))
    (latex_dir / "references.bib").write_text(
        render_references_bib(record.active_literature()) if bib is None else bib
    )


def test_a_citation_of_a_registered_passage_passes_once_judged(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(repo, r"Dropout helps \cite[s1.p1]{vaswani-2017-attention}.")
    _judge(repo, _Judge(lambda where: True))
    result = _verify_paper(str(repo))
    assert result.ok, result.record.problems + result.problems
    assert result.uncited_sources == []


def test_a_citation_of_an_unregistered_key_fails(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(repo, r"As shown \cite{made-up-2020-key}.")
    result = _verify_paper(str(repo))
    assert any("'made-up-2020-key'" in p and "no source" in p for p in result.problems)


def test_a_passage_locator_that_is_not_the_sources_fails(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(repo, r"See \cite[s1.p9]{vaswani-2017-attention}.")
    result = _verify_paper(str(repo))
    assert any("at 's1.p9'" in p for p in result.problems)


def test_a_passage_cited_against_several_keys_fails(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(repo, r"See \cite[s1.p1]{vaswani-2017-attention,other}.")
    result = _verify_paper(str(repo))
    assert any("several keys" in p for p in result.problems)


def test_a_hand_edited_references_bib_fails(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(
        repo,
        r"\cite{vaswani-2017-attention}",
        bib="@article{vaswani-2017-attention,}\n",
    )
    result = _verify_paper(str(repo))
    assert any("references.bib differs" in p for p in result.problems)


def test_sources_never_cited_are_reported_not_failed(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(repo, "No citations at all.")
    _judge(repo, _Judge(lambda where: True))
    result = _verify_paper(str(repo))
    assert result.ok, result.record.problems + result.problems
    assert result.uncited_sources == ["vaswani-2017-attention"]


# ------------------------------------------------ a judge reads the citations


class _Judge:
    """Stands in for the model: supports what `supports` says of `where`."""

    def __init__(self, supports: Any) -> None:
        self.supports = supports
        self.prompts: list[str] = []

    async def structured_output(
        self, llm_name: str, message: str, data_model: Any, **_: Any
    ) -> Any:
        self.prompts.append(message)
        where = message.split("## Citing text (")[1].split(")")[0]
        return data_model(supported=self.supports(where), reason=f"read {where}")


CITED = "Dropout is applied everywhere \\cite[s1.p1]{vaswani-2017-attention}."


def _judge(repo: Path, judge: _Judge) -> int:
    """verify_paper with a model judges what is unjudged; returns how many."""
    before = len(judge.prompts)
    _verify_paper(str(repo), model="judge-1", litellm_client=judge)
    return len(judge.prompts) - before


def test_a_citation_no_judgment_covers_fails_the_gate(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(repo, CITED)
    result = _verify_paper(str(repo))
    assert not result.ok
    assert result.unjudged_citations == [
        r"main.tex \cite[s1.p1]{vaswani-2017-attention} cites s1.p1",
        "hypothesis h1 cites s1.p1",
        "claim c1 cites s1.p1",
    ]
    assert sum("no judgment covers" in p for p in result.problems) == 3
    assert result.unsupported_citations == []


def test_the_judge_reads_every_citation_and_the_gate_reads_the_judgments(
    tmp_path: Path,
) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(repo, CITED + "\n\nUnrelated paragraph.")
    judge = _Judge(lambda where: where.startswith("hypothesis"))

    assert _judge(repo, judge) == 3
    assert _git(repo, "log", "-1", "--format=%s") == "record: judge citations"
    assert [p.split("## Citing text (")[1].split(")")[0] for p in judge.prompts] == [
        r"main.tex \cite[s1.p1]{vaswani-2017-attention}",
        "hypothesis h1",
        "claim c1",
    ]
    # The judge sees the quote in its snapshot, and the paragraph, not the paper.
    assert all("The rate is 0.1." in p for p in judge.prompts)
    assert "Unrelated" not in judge.prompts[0]
    assert "Rationale:" in judge.prompts[2]
    judgments = load_record(str(repo)).literature[0].passages[0].judgments
    assert [(j.supported, j.model) for j in judgments] == [
        (False, "judge-1"),
        (True, "judge-1"),
        (False, "judge-1"),
    ]

    result = _verify_paper(str(repo))
    assert result.ok, result.record.problems + result.problems
    assert result.unjudged_citations == []
    assert result.unsupported_citations == [
        r"main.tex \cite[s1.p1]{vaswani-2017-attention} cites s1.p1: "
        r"read main.tex \cite[s1.p1]{vaswani-2017-attention} (judge-1)",
        "claim c1 cites s1.p1: read claim c1 (judge-1)",
    ]

    # Judged once: nothing to read again.
    assert _judge(repo, judge) == 0

    # A rewritten sentence is a new citation until judged.
    latex_dir = repo / ".research" / "latex" / "mdpi"
    (latex_dir / "main.tex").write_text(
        (latex_dir / "main.tex").read_text().replace("everywhere", "to sub-layers")
    )
    result = _verify_paper(str(repo))
    assert not result.ok
    assert result.unjudged_citations == [
        r"main.tex \cite[s1.p1]{vaswani-2017-attention} cites s1.p1"
    ]
    assert result.unsupported_citations == [
        "claim c1 cites s1.p1: read claim c1 (judge-1)"
    ]


def test_a_clipped_quote_reaches_the_judge_with_what_it_dropped(
    tmp_path: Path,
) -> None:
    _init(tmp_path)
    record = _record()
    record.literature.append(
        LiteratureSource(
            id="s1",
            title="A negative result",
            bibkey="nobody-2020-negative",
            verified_by="doi.org",
            fulltext=write_fulltext(
                tmp_path, "s1", ["We do not find that\ndropout improves accuracy."]
            ),
            passages=[
                QuotedPassage(
                    id="s1.p1", node_type="result", quote="dropout improves accuracy"
                )
            ],
        )
    )
    record.hypotheses[0].grounded_on = ["s1.p1"]
    (citation,) = collect_citations(tmp_path, record, "")
    assert citation.context == "We do not find that dropout improves accuracy."


def test_a_citation_of_an_undeclared_passage_is_left_to_the_gate(
    tmp_path: Path,
) -> None:
    repo, record = _grounded_repo(tmp_path)
    cited = collect_citations(repo, record, r"See \cite[s1.p9]{key}.")
    assert [c.where for c in cited] == ["hypothesis h1", "claim c1"]


def test_a_source_declared_twice_fails(tmp_path: Path) -> None:
    repo, record = _grounded_repo(tmp_path)
    record.literature.append(record.literature[0].model_copy(deep=True))
    record.save(str(repo))
    result = _verify(str(repo))
    assert any("source s1: declared twice" in p for p in result.problems)


def test_a_source_without_a_snapshot_fails(tmp_path: Path) -> None:
    repo, record = _grounded_repo(tmp_path)
    record.literature[0].fulltext = None
    record.literature[0].passages.clear()
    record.hypotheses[0].grounded_on.clear()
    _c1(record).cites_passages.clear()
    record.save(str(repo))
    result = _verify(str(repo))
    assert any("fulltext snapshot must be" in p for p in result.problems)


def test_a_snapshot_outside_its_own_directory_fails(tmp_path: Path) -> None:
    repo, record = _grounded_repo(tmp_path)
    (repo / "elsewhere.txt").write_text(PAGES[1])
    record.literature[0].fulltext.path = "elsewhere.txt"
    record.save(str(repo))
    result = _verify(str(repo))
    assert any("fulltext snapshot must be" in p for p in result.problems)


def test_a_citation_spanning_lines_is_still_checked(tmp_path: Path) -> None:
    repo, _ = _grounded_repo(tmp_path)
    _write_cited_paper(repo, "See \\cite[s1.p1]{\n  made-up-2020-key\n}.")
    result = _verify_paper(str(repo))
    assert any("'made-up-2020-key'" in p for p in result.problems)


def test_two_sources_sharing_a_bibkey_fail(tmp_path: Path) -> None:
    repo, record = _grounded_repo(tmp_path)
    twin = record.literature[0].model_copy(
        deep=True, update={"id": "s2", "passages": []}
    )
    record.literature.append(twin)
    record.save(str(repo))
    result = _verify(str(repo))
    assert any(
        "bibkey 'vaswani-2017-attention' is also source s1's" in p
        for p in result.problems
    )
