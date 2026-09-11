"""verify-paper is the required values gate and never builds; publish-paper
only builds. The two must not drift back into one command."""

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

from airas import cli


def _verify_args(local_path: str) -> argparse.Namespace:
    return argparse.Namespace(
        local_path=local_path,
        template=None,
        no_provenance=False,
        allow_unavailable_provenance=False,
        no_require_paper_values=False,
        allow_unavailable_history=False,
    )


def _publish_args(local_path: str) -> argparse.Namespace:
    return argparse.Namespace(
        local_path=local_path, template=None, output_dir=f"{local_path}/out"
    )


def _exit_code(fn, args) -> int:
    with pytest.raises(SystemExit) as exit:
        fn(args)
    return exit.value.code


def test_paper_gate_passes_when_there_is_no_paper(tmp_path: Path) -> None:
    assert _exit_code(cli._run_verify_paper, _verify_args(str(tmp_path))) == 0


def test_publish_is_a_noop_when_there_is_no_paper(tmp_path: Path) -> None:
    assert _exit_code(cli._run_publish_paper, _publish_args(str(tmp_path))) == 0


def test_a_paper_under_an_unsupported_template_is_not_no_paper(
    tmp_path: Path,
) -> None:
    # A main.tex the gate cannot verify must fail, not pass as "no paper yet".
    (tmp_path / ".research" / "latex" / "homebrew").mkdir(parents=True)
    (tmp_path / ".research" / "latex" / "homebrew" / "main.tex").write_text("x")
    assert _exit_code(cli._run_verify_paper, _verify_args(str(tmp_path))) == 1
    assert _exit_code(cli._run_publish_paper, _publish_args(str(tmp_path))) == 1


@pytest.mark.parametrize("ok", [True, False])
def test_publish_builds_and_reports_the_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ok: bool
) -> None:
    calls: list[tuple[str, ...]] = []

    def build(*args: str) -> SimpleNamespace:
        calls.append(args)
        return SimpleNamespace(ok=ok, model_dump=dict)

    monkeypatch.setattr(cli, "detect_templates", lambda _p: ["mdpi"])
    monkeypatch.setattr(cli, "build_paper", build)
    code = _exit_code(cli._run_publish_paper, _publish_args(str(tmp_path)))
    assert code == (0 if ok else 1)
    assert calls == [(str(tmp_path), "mdpi", str(tmp_path / "out" / "mdpi.pdf"))]


def test_the_gate_verifies_without_building(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "detect_templates", lambda _p: ["mdpi"])
    monkeypatch.setattr(
        cli, "build_paper", lambda *a: pytest.fail("the gate must not build")
    )

    async def verified(*_a, **_k):
        return SimpleNamespace(ok=True, model_dump=dict)

    monkeypatch.setattr(cli, "verify_paper", verified)
    assert _exit_code(cli._run_verify_paper, _verify_args(str(tmp_path))) == 0
