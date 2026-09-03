import json
from pathlib import Path

import pytest

from airas.core.types.paper_values import PaperValue
from airas.core.types.research_record import (
    Bound,
    ClaimDeclaration,
    DesignDeclaration,
    Hypothesis,
    LinkBase,
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
    compute_claim_values,
    load_metrics_data,
    resolve_paper_ref,
    resolve_paper_values,
)
from airas.usecases.publication.paper_values.latex import render_values_tex
from airas.usecases.publication.paper_values.realize import realize_record
from airas.usecases.publication.paper_values.record import (
    orphan_runs,
    override_problems,
    record_consistency_problems,
    save_record,
)
from airas.usecases.publication.paper_values.verify import (
    _scan_main_tex,
    merge_paper_values_report,
    paper_values_configured,
    verify_paper_record,
)

TEMPLATE = "mdpi"

MAIN_TEX = "\n".join(
    [
        r"\documentclass{article}",
        r"\input{values.tex}",
        r"\begin{document}",
        r"The gain is \airasval{c1.value}. % comment with 3.3",
        r"Run 1 scored \airasval{run-1.accuracy} at batch"
        r" \airasval{run-1.params.batch_size} on \airasval{run-1.params.dataset}.",
        r"Prior work reports \unverified{12345} samples.",
        r"A raw 99.9 that should be flagged.",
        r"\end{document}",
        "",
    ]
)


def _record() -> ResearchRecord:
    """Two runs, one claim judged on the improvement between them."""
    return ResearchRecord(
        hypothesis=Hypothesis(
            statement="Method X improves accuracy.",
            claims=[
                ClaimDeclaration(
                    id="c1",
                    statement="X beats the baseline.",
                    target=Target(
                        op="pct_improve",
                        refs=["run-2.accuracy", "run-1.accuracy"],
                        round=1,
                    ),
                    criterion=Bound(min=0.0),
                    predicted_interval=Bound(min=2.0, max=4.0),
                    rationale="2-4 points, from prior work",
                )
            ],
            designs=[
                DesignDeclaration(
                    id="d1",
                    summary="Two runs on the same dataset.",
                    runs=[
                        RunDeclaration(run_id="run-1", overrides={"mode": "full"}),
                        RunDeclaration(run_id="run-2"),
                    ],
                )
            ],
        )
    )


def _manifest(mode: str = "full") -> RunProvenanceManifest:
    return RunProvenanceManifest(
        dirs={
            "run-1": ResultsDirProvenance(
                execution_id="exec-1",
                commit_hash="c" * 40,
                overrides={"mode": mode},
                # What Seyval reports the run actually resolved.
                parameters={
                    "mode": mode,
                    "batch_size": "128",
                    "dataset": "cifar10",
                },
            ),
            "run-2": ResultsDirProvenance(execution_id="exec-2", commit_hash="c" * 40),
        }
    )


def _make_repo(tmp_path: Path) -> Path:
    results = tmp_path / ".research" / "results"
    (results / "run-1").mkdir(parents=True)
    (results / "run-2").mkdir()
    (results / "run-1" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.871, "loss": {"final": 0.32}})
    )
    (results / "run-2" / "metrics.json").write_text(json.dumps({"accuracy": 0.902}))
    latex_dir = tmp_path / ".research" / "latex" / TEMPLATE
    latex_dir.mkdir(parents=True)
    return latex_dir


def _generate(tmp_path: Path, mode: str = "full") -> Path:
    latex_dir = _make_repo(tmp_path)
    record = _record()
    metrics_data = load_metrics_data(str(tmp_path))
    manifest = _manifest(mode)
    # On disk as import_run_outputs leaves it: verification reads the file,
    # and an execution the manifest does not declare is a finding.
    (tmp_path / PROVENANCE_MANIFEST_PATH).write_text(
        manifest.model_dump_json(indent=2) + "\n"
    )
    realize_record(tmp_path, record, metrics_data, manifest)
    save_record(str(tmp_path), record)

    (latex_dir / "main.tex").write_text(MAIN_TEX)
    used_keys = _scan_main_tex(MAIN_TEX)[1]
    values, _ = resolve_paper_values(record, metrics_data, used_keys)
    (latex_dir / "values.tex").write_text(render_values_tex(values, None))
    return latex_dir


# --------------------------------------------------------------- resolution


def test_claim_target_is_computed_from_the_runs(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    metrics_data = load_metrics_data(str(tmp_path))
    value, display, used = compute_claim_values(_record(), metrics_data)["c1"]

    assert value == pytest.approx((0.902 - 0.871) / 0.871 * 100)
    assert display == "3.6"
    assert used == {}  # no executions recorded yet


def test_paper_refs_resolve_claims_metrics_and_parameters(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    record = _record()
    metrics_data = load_metrics_data(str(tmp_path))
    realize_record(tmp_path, record, metrics_data, _manifest())

    resolve = lambda ref: resolve_paper_ref(record, metrics_data, ref)  # noqa: E731
    assert resolve("c1.value") == "3.6"
    assert resolve("run-1.accuracy") == "0.871"
    assert resolve("run-1.loss.final") == "0.32"
    assert resolve("run-1.params.batch_size") == "128"
    # Config values are legitimately strings and must survive unrounded.
    assert resolve("run-1.params.dataset") == "cifar10"


def test_paper_ref_rejects_unknown_run(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    metrics_data = load_metrics_data(str(tmp_path))
    with pytest.raises(ValueError, match="matches no run id"):
        resolve_paper_ref(_record(), metrics_data, "run-9.accuracy")


def test_parameter_ref_needs_an_execution(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    metrics_data = load_metrics_data(str(tmp_path))
    with pytest.raises(ValueError, match="no execution"):
        resolve_paper_ref(_record(), metrics_data, "run-1.params.batch_size")


# ------------------------------------------------------------- realization


def test_executions_are_appended_not_replaced(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    record = _record()
    metrics_data = load_metrics_data(str(tmp_path))

    _, first = realize_record(tmp_path, record, metrics_data, _manifest())
    assert first == 2

    # Re-realizing the same outputs must not grow the record: only a genuinely
    # different execution is a new fact.
    _, again = realize_record(tmp_path, record, metrics_data, _manifest())
    assert again == 0

    # A re-run with different numbers appends rather than overwriting, so the
    # earlier result stays in the record.
    (tmp_path / ".research" / "results" / "run-2" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.950})
    )
    metrics_data = load_metrics_data(str(tmp_path))
    _, rerun = realize_record(tmp_path, record, metrics_data, _manifest())
    assert rerun == 1

    run2 = record.hypothesis.designs[0].runs[1]
    assert [e.metrics["accuracy"] for e in run2.executions] == [0.902, 0.950]


def test_execution_records_inputs_evaluation_and_parameters(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    results = tmp_path / ".research" / "results" / "run-1"
    (results / "eval_inputs").mkdir()
    (results / "eval_inputs" / "classification.json").write_text(
        json.dumps({"predicted_labels": [1, 0], "reference_labels": [1, 1]})
    )
    (results / "evaluation").mkdir()
    (results / "evaluation" / "classification.json").write_text(
        json.dumps(
            {
                "task_type": "classification",
                "metrics": {"accuracy": 0.5},
                "skipped": {"auroc": "not binary"},
                "provenance": {
                    "task_signature": "classification/v1@abc",
                    "inputs_sha256": "deadbeef",
                    "versions": {"airas-eval": "0.10.0"},
                },
            }
        )
    )
    record = _record()
    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), _manifest())

    execution = record.hypothesis.designs[0].runs[0].executions[-1]
    assert execution.execution_id == "exec-1"
    assert execution.overrides == {"mode": "full"}
    # From the platform's report, not from a file the run wrote.
    assert execution.parameters == {
        "mode": "full",
        "batch_size": "128",
        "dataset": "cifar10",
    }
    assert execution.inputs is not None and len(execution.inputs.sha256) == 64
    assert execution.evaluation is not None
    # A metric that could not be computed is a result too.
    assert execution.evaluation.skipped == {"auroc": "not binary"}
    assert execution.evaluation.versions == {"airas-eval": "0.10.0"}


def test_criterion_is_evaluated_apart_from_verification(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    record = _record()
    statuses, _ = realize_record(
        tmp_path, record, load_metrics_data(str(tmp_path)), _manifest()
    )
    status = statuses[0]

    # The gain is positive, so the criterion holds...
    assert status.criterion_met is True
    # ...but tmp_path is not a git repo, so the order proof cannot be made and
    # the claim is not verified. The two are independent by design.
    assert status.verified is False


def test_refuted_claim_is_verifiable_and_unmet(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    # Make the "improvement" negative so the criterion fails.
    (tmp_path / ".research" / "results" / "run-2" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.800})
    )
    record = _record()
    statuses, _ = realize_record(
        tmp_path, record, load_metrics_data(str(tmp_path)), _manifest()
    )
    assert statuses[0].criterion_met is False
    assert record.hypothesis.claims[0].evaluations[-1].criterion_met is False


# ------------------------------------------------------------- declarations


def test_claim_referencing_an_undeclared_run_is_rejected() -> None:
    record = _record()
    record.hypothesis.claims[0].target.refs = ["run-9.accuracy", "run-1.accuracy"]
    problems = record_consistency_problems(record)
    assert any("run-9" in p for p in problems)


def test_unbounded_criterion_is_rejected() -> None:
    record = _record()
    record.hypothesis.claims[0].criterion = Bound()
    assert any("unbounded" in p for p in record_consistency_problems(record))


def test_run_declared_in_two_designs_is_rejected() -> None:
    record = _record()
    record.hypothesis.designs.append(
        DesignDeclaration(id="d2", runs=[RunDeclaration(run_id="run-1")])
    )
    assert any("repo-unique" in p for p in record_consistency_problems(record))


def test_orphan_runs_are_listed_not_rejected() -> None:
    record = _record()
    record.hypothesis.designs[0].runs.append(RunDeclaration(run_id="run-3"))
    assert record_consistency_problems(record) == []
    assert orphan_runs(record) == ["run-3"]


def test_declared_override_must_match_the_dispatch(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    record = _record()
    metrics_data = load_metrics_data(str(tmp_path))

    realize_record(tmp_path, record, metrics_data, _manifest(mode="full"))
    assert override_problems(record) == []

    # Declaring `full` and dispatching `pilot` runs a fraction of the planned
    # scale without changing a tracked file: only this comparison shows it.
    other = _record()
    realize_record(tmp_path, other, metrics_data, _manifest(mode="pilot"))
    problems = override_problems(other)
    assert any("declared 'mode=full' but executed 'mode=pilot'" in p for p in problems)


def test_a_declared_parameter_missing_from_a_complete_report_is_a_problem(
    tmp_path: Path,
) -> None:
    """The platform listed everything the run resolved, and it was not there."""
    _make_repo(tmp_path)
    record = _record()
    manifest = _manifest()
    manifest.dirs["run-1"].parameters = {"batch_size": "128"}  # no `mode`
    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)

    assert override_problems(record) == [
        "run 'run-1': declared 'mode=full' but the execution resolved no such parameter"
    ]


def test_a_declared_parameter_absent_from_overrides_alone_is_not_a_problem(
    tmp_path: Path,
) -> None:
    """Overrides carry only what the dispatch restated.

    A parameter left at the commit's default never appears there, so absence
    is unknown rather than wrong — reporting it would fail every run that
    took a declared value from its default.
    """
    _make_repo(tmp_path)
    record = _record()
    manifest = _manifest()
    manifest.dirs["run-1"].parameters = {}  # platform reported no full set
    manifest.dirs["run-1"].overrides = {}  # and the dispatch restated nothing
    realize_record(tmp_path, record, load_metrics_data(str(tmp_path)), manifest)

    assert override_problems(record) == []


# ------------------------------------------------------------------- latex


def test_values_tex_defines_each_ref(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    tex = (latex_dir / "values.tex").read_text()
    assert "AUTO-GENERATED" in tex
    for ref in ("c1.value", "run-1.accuracy", "run-1.params.batch_size"):
        assert f"airasval@{ref}" in tex
    assert "cifar10" in tex


def test_values_tex_pins_the_link_to_a_commit() -> None:
    values = [PaperValue(ref="c1.value", display="3.6")]
    base = LinkBase(repo_url="https://github.com/org/repo")

    linked = render_values_tex(values, base, "abc123")
    assert r"\href{https://github.com/org/repo/blob/abc123/.research/record.json}" in (
        linked
    )
    # Without a commit there is nothing to pin to, so no link is emitted
    # rather than one that would drift with the branch.
    assert r"\href" not in render_values_tex(values, base, None)
    assert r"\href" not in render_values_tex(values, None, "abc123")


def test_values_tex_drops_latex_hostile_link() -> None:
    tex = render_values_tex(
        [PaperValue(ref="c1.value", display="3.6")],
        LinkBase(repo_url="https://github.com/org/repo"),
        "feat%branch",
    )
    assert r"\href" not in tex


# ------------------------------------------------------------ verification


def test_verify_ok_on_fresh_generation(tmp_path: Path) -> None:
    _generate(tmp_path)
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert report.ok
    assert report.stage == "results"
    assert report.values_tex_match
    assert report.unverified == ["12345"]
    assert report.provenance is None
    # tmp_path is not a git repo: history is unavailable (CI enforces it),
    # and no claim can be verified without the order proof.
    assert report.append_only == "unavailable"
    assert report.unverified_claims == ["c1"]


def test_verify_detects_edited_values_tex(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    values_tex = latex_dir / "values.tex"
    values_tex.write_text(values_tex.read_text().replace("0.871", "0.971"))
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert not report.values_tex_match


def test_verify_detects_tampered_metrics(tmp_path: Path) -> None:
    _generate(tmp_path)
    metrics_path = tmp_path / ".research" / "results" / "run-2" / "metrics.json"
    metrics_path.write_text(json.dumps({"accuracy": 0.95}))
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert not report.ok
    # The recomputed claim no longer matches the stored evaluation.
    assert any("claim evaluations" in m for m in report.mismatches)


def test_verify_reports_missing_files(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert len(report.missing_files) == 3


def test_verify_detects_undefined_key(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    main_tex = latex_dir / "main.tex"
    main_tex.write_text(
        main_tex.read_text().replace(
            r"\airasval{c1.value}", r"\airasval{c1.value} and \airasval{no_such_key}"
        )
    )
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert report.undefined_keys == ["no_such_key"]


def test_verify_rejects_undeclared_results_dir(tmp_path: Path) -> None:
    _generate(tmp_path)
    rogue = tmp_path / ".research" / "results" / "run-3"
    rogue.mkdir()
    (rogue / "metrics.json").write_text(json.dumps({"accuracy": 0.99}))
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert report.undeclared_result_dirs == ["run-3"]


def test_verify_prereg_stage_passes_without_results(tmp_path: Path) -> None:
    latex_dir = tmp_path / ".research" / "latex" / TEMPLATE
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    save_record(str(tmp_path), _record())
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert report.stage == "prereg"
    assert report.ok
    assert report.unverified_claims == ["c1"]
    assert report.undefined_keys == []  # placeholders are the prereg state


def test_verify_prereg_stage_rejects_leftover_values_tex(tmp_path: Path) -> None:
    latex_dir = tmp_path / ".research" / "latex" / TEMPLATE
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    (latex_dir / "values.tex").write_text("stale realized numbers")
    save_record(str(tmp_path), _record())
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert any("no run outputs exist" in m for m in report.mismatches)


def test_verify_prereg_stage_rejects_premature_results(tmp_path: Path) -> None:
    latex_dir = tmp_path / ".research" / "latex" / TEMPLATE
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    record = _record()
    record.hypothesis.designs[0].runs[0].executions.append(
        __import__(
            "airas.core.types.research_record", fromlist=["Execution"]
        ).Execution(execution_id="exec-1", metrics={"accuracy": 0.9})
    )
    save_record(str(tmp_path), record)
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert any("no run outputs exist" in m for m in report.mismatches)


def test_merge_gates_latex_ok_when_configured(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert paper_values_configured(report)
    assert merge_paper_values_report({"ok": True}, report)["ok"] is True

    values_tex = latex_dir / "values.tex"
    values_tex.write_text(values_tex.read_text().replace("0.871", "0.971"))
    tampered = verify_paper_record(str(tmp_path), TEMPLATE)
    merged = merge_paper_values_report({"ok": True}, tampered)
    assert merged["ok"] is False
    assert merged["paper_values_configured"] is True


def test_merge_passes_through_when_not_configured(tmp_path: Path) -> None:
    _make_repo(tmp_path)  # no record.json / values.tex / main.tex
    report = verify_paper_record(str(tmp_path), TEMPLATE)
    assert not paper_values_configured(report)
    merged = merge_paper_values_report({"ok": True}, report)
    assert merged["ok"] is True
    assert merged["paper_values_configured"] is False


def test_comment_stripping_honours_backslash_parity() -> None:
    from airas.usecases.publication.paper_values.verify import _strip_comment

    # \% is a literal percent: the line continues past it.
    assert _strip_comment(r"a \% literal % comment") == r"a \% literal "
    # \\% is a line break followed by a comment: strip from the %.
    assert _strip_comment(r"break \\% comment") == "break \\\\"
    # \\\% is a line break then a literal percent: no comment here.
    assert _strip_comment(r"keep \\\% text") == r"keep \\\% text"
    assert _strip_comment("no comment at all") == "no comment at all"


def test_scan_ignores_macros_commented_out_after_linebreak() -> None:
    from airas.usecases.publication.paper_values.verify import _scan_main_tex

    unverified, used_keys = _scan_main_tex(
        "line \\\\% \\airasval{ghost} \\unverified{ghost claim}\n"
        "real \\airasval{acc} and \\% \\unverified{kept}"
    )
    assert used_keys == ["acc"]
    assert unverified == ["kept"]
