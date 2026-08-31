import json
from pathlib import Path

import pytest

from airas.core.types.paper_values import ValueDeclaration
from airas.usecases.publication.paper_values.compute import (
    compute_paper_values,
    load_metrics_data,
)
from airas.usecases.publication.paper_values.latex import render_values_tex
from airas.usecases.publication.paper_values.verify import (
    merge_paper_values_report,
    paper_values_configured,
    verify_paper_values,
)

TEMPLATE = "mdpi"

DECLARATIONS = [
    ValueDeclaration(key="acc_run1", refs=["run-1.accuracy"], round=3),
    ValueDeclaration(
        key="acc_mean",
        op="mean",
        refs=["run-1.accuracy", "run-2.accuracy"],
        round=3,
    ),
    ValueDeclaration(
        key="acc_gain",
        op="pct_improve",
        refs=["run-2.accuracy", "run-1.accuracy"],
        round=1,
    ),
    ValueDeclaration(key="final_loss", refs=["run-1.loss.final"]),
]

MAIN_TEX = "\n".join(
    [
        r"\documentclass{article}",
        r"\input{values.tex}",
        r"\begin{document}",
        r"Accuracy is \airasval{acc_mean}. % comment with 3.3",
        r"Prior work reports \unverified{12345} samples.",
        r"A raw 99.9 that should be flagged.",
        r"\end{document}",
        "",
    ]
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


def _generate(tmp_path: Path) -> Path:
    latex_dir = _make_repo(tmp_path)
    metrics_data = load_metrics_data(str(tmp_path))
    paper_values = compute_paper_values(DECLARATIONS, metrics_data)
    (latex_dir / "values.json").write_text(paper_values.model_dump_json(indent=2))
    (latex_dir / "values.tex").write_text(render_values_tex(paper_values))
    (latex_dir / "main.tex").write_text(MAIN_TEX)
    return latex_dir


def test_compute_evaluates_ops_and_rounds(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    metrics_data = load_metrics_data(str(tmp_path))
    paper_values = compute_paper_values(DECLARATIONS, metrics_data)
    by_key = {v.key: v for v in paper_values.values}

    assert by_key["acc_run1"].display == "0.871"
    assert by_key["acc_mean"].value == pytest.approx((0.871 + 0.902) / 2)
    assert by_key["acc_mean"].display == f"{by_key['acc_mean'].value:.3f}"
    assert by_key["acc_gain"].value == pytest.approx((0.902 - 0.871) / 0.871 * 100)
    assert by_key["acc_gain"].display == "3.6"
    assert by_key["final_loss"].display == "0.32"


def test_compute_rejects_unknown_ref(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    metrics_data = load_metrics_data(str(tmp_path))
    with pytest.raises(ValueError, match="matches no run id"):
        compute_paper_values(
            [ValueDeclaration(key="bad", refs=["run-9.accuracy"])],
            metrics_data,
        )


def test_values_tex_defines_each_key(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    paper_values = compute_paper_values(DECLARATIONS, load_metrics_data(str(tmp_path)))
    tex = render_values_tex(paper_values)
    assert "AUTO-GENERATED" in tex
    for value in paper_values.values:
        assert f"airasval@{value.key}" in tex
        assert value.display in tex


def test_verify_ok_on_fresh_generation(tmp_path: Path) -> None:
    _generate(tmp_path)
    report = verify_paper_values(str(tmp_path), TEMPLATE)
    assert report.ok
    assert report.values_match
    assert report.values_tex_match
    assert report.unverified == ["12345"]
    assert report.provenance is None


def test_verify_detects_edited_values_tex(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    values_tex = latex_dir / "values.tex"
    values_tex.write_text(values_tex.read_text().replace("0.871", "0.971"))
    report = verify_paper_values(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert report.values_match
    assert not report.values_tex_match


def test_verify_detects_tampered_metrics(tmp_path: Path) -> None:
    _generate(tmp_path)
    metrics_path = tmp_path / ".research" / "results" / "run-2" / "metrics.json"
    metrics_path.write_text(json.dumps({"accuracy": 0.95}))
    report = verify_paper_values(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert not report.values_match
    assert any("acc_mean" in m for m in report.mismatches)


def test_verify_reports_missing_files(tmp_path: Path) -> None:
    _make_repo(tmp_path)
    report = verify_paper_values(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert len(report.missing_files) == 3


def test_verify_detects_undefined_key(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    main_tex = latex_dir / "main.tex"
    main_tex.write_text(
        main_tex.read_text().replace(
            r"\airasval{acc_mean}",
            r"\airasval{acc_mean} and \airasval{no_such_key}",
        )
    )
    report = verify_paper_values(str(tmp_path), TEMPLATE)
    assert not report.ok
    assert report.undefined_keys == ["no_such_key"]


def test_merge_gates_latex_ok_when_configured(tmp_path: Path) -> None:
    latex_dir = _generate(tmp_path)
    report = verify_paper_values(str(tmp_path), TEMPLATE)
    assert paper_values_configured(report)
    assert merge_paper_values_report({"ok": True}, report)["ok"] is True

    values_tex = latex_dir / "values.tex"
    values_tex.write_text(values_tex.read_text().replace("0.871", "0.971"))
    tampered = verify_paper_values(str(tmp_path), TEMPLATE)
    merged = merge_paper_values_report({"ok": True}, tampered)
    assert merged["ok"] is False
    assert merged["paper_values_configured"] is True


def test_merge_passes_through_when_not_configured(tmp_path: Path) -> None:
    _make_repo(tmp_path)  # no values.json / values.tex / main.tex
    report = verify_paper_values(str(tmp_path), TEMPLATE)
    assert not paper_values_configured(report)
    merged = merge_paper_values_report({"ok": True}, report)
    assert merged["ok"] is True
    assert merged["paper_values_configured"] is False
