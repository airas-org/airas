"""verify-paper is the required values gate and never builds; publish-paper
only builds. The two must not drift back into one command."""

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from airas import cli
from airas.core.types.record_verification import RecordVerification


def _verify_args(local_path: str) -> argparse.Namespace:
    return argparse.Namespace(
        local_path=local_path,
        template=None,
        citation_verifier_model=None,
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
    monkeypatch.setattr(
        cli, "verify_record", lambda *a, **k: pytest.fail("record has its own gate")
    )

    async def verified(*_a, **_k):
        return SimpleNamespace(ok=True, model_dump=dict)

    monkeypatch.setattr(cli, "verify_paper", verified)
    assert _exit_code(cli._run_verify_paper, _verify_args(str(tmp_path))) == 0


def test_record_gate_accepts_an_implementation_review_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".research").mkdir()
    calls = []
    client = object()

    async def verified(*args, **kwargs):
        calls.append(kwargs)
        return RecordVerification()

    monkeypatch.setattr(cli, "verify_record", verified)
    monkeypatch.setattr(cli, "LiteLLMClient", lambda: client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "airas",
            "verify-record",
            "--local-path",
            str(tmp_path),
            "--implementation-verifier-model",
            "review-model",
        ],
    )
    with pytest.raises(SystemExit) as exit:
        cli.main()
    assert exit.value.code == 0
    assert calls[0]["implementation_verifier_model"] == "review-model"
    assert calls[0]["litellm_client"] is client


def test_an_unsupported_template_fails_even_beside_a_known_one(
    tmp_path: Path,
) -> None:
    # A known template must not hide a paper the gate cannot verify.
    for name in ("mdpi", "homebrew"):
        (tmp_path / ".research" / "latex" / name).mkdir(parents=True)
        (tmp_path / ".research" / "latex" / name / "main.tex").write_text("x")
    assert _exit_code(cli._run_verify_paper, _verify_args(str(tmp_path))) == 1
    assert _exit_code(cli._run_publish_paper, _publish_args(str(tmp_path))) == 1
