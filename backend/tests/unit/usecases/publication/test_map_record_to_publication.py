"""From run outputs to the paper's numbers, and the checks along the way.

The paper's numbers resolve from the files (`<run_id>.<metric>`) and the
declarations (`<run_id>.params.<key>`); `update_record_with_results` appends what the
runs produced; `verify_paper_record` regenerates values.tex and rejects a
paper whose numbers drift from either.
"""

import asyncio
import json
from pathlib import Path

import pytest

from airas.core.types.map_record_to_publication import (
    TableColumnSpec,
    TableRowSpec,
    TableSpec,
)
from airas.core.types.research_record import (
    Hypothesis,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
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
    record_blob_url,
    render_values_tex,
    resolve_paper_ref,
    resolve_paper_values,
)
from airas.usecases.publication.verify_paper import scan_main_tex, verify_paper
from airas.usecases.recording.update_or_load_record import (
    load_metrics_data,
    save_record,
    update_record_with_results,
)

SEYVAL = SeyvalVerifier(kind=VerifierKind.SEYVAL)

TEMPLATE = "mdpi"

MAIN_TEX = "\n".join(
    [
        r"\documentclass{article}",
        r"\input{values.tex}",
        r"\begin{document}",
        r"Run 1 scored \airasval{run-1.accuracy} (loss \airasval{run-1.loss.final})"
        r" at batch \airasval{run-1.params.batch_size} on"
        r" \airasval{run-1.params.dataset}. % comment with 3.3",
        r"Prior work reports \unverified{12345} samples.",
        r"A raw 99.9 that should be flagged.",
        r"\end{document}",
        "",
    ]
)


def _record() -> ResearchRecord:
    """One claim, two runs under one design."""
    return ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="Method X improves accuracy.",
                claims=[
                    SeyvalClaim(
                        verifier=SEYVAL,
                        id="c1",
                        statement="X beats the baseline.",
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                summary="Two runs on the same dataset.",
                                runs=[
                                    SeyvalRun(
                                        run_id="run-1",
                                        params={
                                            "mode": "full",
                                            "batch_size": 128,
                                            "dataset": "cifar10",
                                        },
                                    ),
                                    SeyvalRun(run_id="run-2"),
                                ],
                            )
                        ],
                    )
                ],
                tables=[
                    TableSpec(
                        key="main_results",
                        caption="Results.",
                        columns=[
                            TableColumnSpec(
                                header="Accuracy", ref_path="accuracy", round=3
                            )
                        ],
                        rows=[
                            TableRowSpec(run_id="run-2", label="Ours"),
                            TableRowSpec(run_id="run-1", label="Baseline"),
                        ],
                    )
                ],
            )
        ]
    )


def _manifest(mode: str = "full") -> RunProvenanceManifest:
    return RunProvenanceManifest(
        dirs={
            "run-1": ResultsDirProvenance(
                execution_id="exec-1",
                commit_hash="c" * 40,
                overrides={"mode": mode},
                parameters={"mode": mode, "batch_size": "128", "dataset": "cifar10"},
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
    # and a result the manifest does not declare is a finding.
    (tmp_path / PROVENANCE_MANIFEST_PATH).write_text(
        manifest.model_dump_json(indent=2) + "\n"
    )
    update_record_with_results(tmp_path, record, metrics_data, manifest)
    save_record(str(tmp_path), record)

    (latex_dir / "main.tex").write_text(MAIN_TEX)
    used_keys = scan_main_tex(MAIN_TEX)[1]
    values, _ = resolve_paper_values(record, metrics_data, used_keys)
    (latex_dir / "values.tex").write_text(render_values_tex(values, None))
    from airas.usecases.publication.map_record_to_publication import render_table_tex

    tables_dir = latex_dir / "tables"
    tables_dir.mkdir()
    for spec in record.hypotheses[0].tables:
        (tables_dir / f"{spec.key}.tex").write_text(
            render_table_tex(spec, metrics_data)
        )
    return latex_dir


# --------------------------------------------------------------- resolution


def test_paper_refs_resolve_metrics_and_declared_params(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    record = _record()
    metrics_data = load_metrics_data(str(tmp_path))

    resolve = lambda ref: resolve_paper_ref(record, metrics_data, ref)  # noqa: E731
    assert resolve("run-1.accuracy") == "0.871"
    assert resolve("run-1.loss.final") == "0.32"
    assert resolve("run-1.params.batch_size") == "128"
    # Declared values are legitimately strings and must survive unrounded.
    assert resolve("run-1.params.dataset") == "cifar10"


def test_paper_ref_rejects_unknown_run(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    metrics_data = load_metrics_data(str(tmp_path))
    with pytest.raises(ValueError, match="matches no run id"):
        resolve_paper_ref(_record(), metrics_data, "run-9.accuracy")


def test_param_ref_rejects_an_undeclared_key(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    metrics_data = load_metrics_data(str(tmp_path))
    with pytest.raises(ValueError, match="declares no such parameter"):
        resolve_paper_ref(_record(), metrics_data, "run-1.params.seed")


def test_undefined_keys_are_reported_not_raised(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    values, undefined = resolve_paper_values(
        _record(), load_metrics_data(str(tmp_path)), ["run-1.accuracy", "ghost.x"]
    )
    assert [v.ref for v in values] == ["run-1.accuracy"]
    assert undefined == ["ghost.x"]


# ------------------------------------------------------------- realization


def test_results_are_appended_not_replaced(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    record = _record()
    metrics_data = load_metrics_data(str(tmp_path))

    _, first = update_record_with_results(tmp_path, record, metrics_data, _manifest())
    assert first == 2

    # Re-realizing the same outputs must not grow the record: only a
    # genuinely different result is a new fact.
    _, again = update_record_with_results(tmp_path, record, metrics_data, _manifest())
    assert again == 0

    # A re-run with different numbers appends rather than overwriting.
    (tmp_path / ".research" / "results" / "run-2" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.950})
    )
    metrics_data = load_metrics_data(str(tmp_path))
    _, rerun = update_record_with_results(tmp_path, record, metrics_data, _manifest())
    assert rerun == 1

    run2 = record.hypotheses[0].claims[0].designs[0].runs[1]
    assert [r.metrics["accuracy"] for r in run2.results] == [0.902, 0.950]


def test_a_result_records_inputs_report_and_metrics(tmp_path: Path) -> None:
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
                "metrics": {"accuracy": 0.871},
                "skipped": {"auroc": "single class"},
                "provenance": {"versions": {"airas-eval": "0.4.0"}},
            }
        )
    )
    record = _record()
    update_record_with_results(
        tmp_path, record, load_metrics_data(str(tmp_path)), _manifest()
    )

    result = record.hypotheses[0].claims[0].designs[0].runs[0].results[-1]
    assert result.id == "exec-1"
    assert result.commit == "c" * 40
    assert result.eval_inputs is not None
    assert result.eval_inputs.path.endswith("eval_inputs/classification.json")
    assert len(result.eval_inputs.sha256) == 64
    assert result.eval_report is not None
    assert result.eval_report.skipped == {"auroc": "single class"}
    assert result.eval_report.versions == {"airas-eval": "0.4.0"}
    assert result.metrics == {"accuracy": 0.871, "loss": {"final": 0.32}}


def test_a_run_the_manifest_does_not_declare_gets_no_result(tmp_path: Path) -> None:
    """A result is the platform's fact; without the manifest there is none."""
    _make_repo(tmp_path)
    record = _record()
    manifest = _manifest()
    del manifest.dirs["run-2"]
    _, appended = update_record_with_results(
        tmp_path, record, load_metrics_data(str(tmp_path)), manifest
    )
    assert appended == 1
    assert record.hypotheses[0].claims[0].designs[0].runs[1].results == []


# ------------------------------------------------------------------- latex


def test_values_tex_links_each_value_to_the_commit(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    values, _ = resolve_paper_values(
        _record(), load_metrics_data(str(tmp_path)), ["run-1.accuracy"]
    )
    tex = render_values_tex(values, "https://github.com/o/r", "a" * 40)
    assert "airasval@run-1.accuracy" in tex
    assert f"https://github.com/o/r/blob/{'a' * 40}/.research/record.json" in tex


def test_no_link_without_an_origin_or_a_commit() -> None:
    assert record_blob_url(None, "a" * 40) is None
    assert record_blob_url("https://github.com/o/r", None) is None


# ------------------------------------------------------------ verification


def _verify(path: str):
    return asyncio.run(
        verify_paper(path, TEMPLATE, check_provenance=False, require_history=False)
    )


def test_verify_ok_on_fresh_generation(tmp_path: Path) -> None:
    _generate(tmp_path)
    result = _verify(str(tmp_path))
    assert result.ok, result.record.problems + result.problems
    assert result.unverified == ["12345"]


def test_verify_detects_tampered_metrics(tmp_path: Path) -> None:
    _generate(tmp_path)
    (tmp_path / ".research" / "results" / "run-2" / "metrics.json").write_text(
        json.dumps({"accuracy": 0.95})
    )
    result = _verify(str(tmp_path))
    assert not result.ok
    # The result's copy no longer matches the file, and the table differs.
    assert any("metrics differ" in p for p in result.record.problems)


def test_verify_detects_edited_values_tex(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    values_tex = latex_dir / "values.tex"
    values_tex.write_text(values_tex.read_text().replace("0.871", "0.999"))
    result = _verify(str(tmp_path))
    assert not result.ok
    assert any("differs from its regeneration" in p for p in result.problems)


def test_verify_flags_undeclared_keys(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    (latex_dir / "main.tex").write_text(
        MAIN_TEX.replace(r"\airasval{run-1.accuracy}", r"\airasval{run-9.accuracy}")
    )
    result = _verify(str(tmp_path))
    assert not result.ok
    assert any("run-9.accuracy" in p for p in result.problems)


def test_verify_detects_dispatch_under_other_conditions(tmp_path: Path) -> None:
    """Declared mode=full; the platform recorded mode=pilot."""
    _generate(tmp_path, mode="pilot")
    result = _verify(str(tmp_path))
    assert not result.ok
    assert any("executed 'mode=pilot'" in p for p in result.record.problems)


def test_prereg_stage_rejects_leftover_values_tex(tmp_path: Path) -> None:
    latex_dir = tmp_path / ".research" / "latex" / TEMPLATE
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    (latex_dir / "values.tex").write_text("% stale\n")
    save_record(str(tmp_path), _record())
    result = _verify(str(tmp_path))
    assert result.record.stage == "prereg"
    assert not result.ok
    assert any("values.tex exists" in p for p in result.problems)


def test_a_paper_without_a_record_passes_only_when_not_required(tmp_path: Path) -> None:
    latex_dir = tmp_path / ".research" / "latex" / TEMPLATE
    latex_dir.mkdir(parents=True)
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    result = _verify(str(tmp_path))
    assert not result.ok
    assert any("record.json is missing" in p for p in result.problems)
    relaxed = asyncio.run(
        verify_paper(
            str(tmp_path), TEMPLATE, check_provenance=False, require_record=False
        )
    )
    assert relaxed.ok
