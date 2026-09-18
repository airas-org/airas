"""fetch_paper_reproduction_results: the run's self-report plus the backend's
verdict, and a fixed return shape on every failure path."""

from typing import Any

import pytest

from airas.core.llm_config import NodeLLMConfig
from airas.core.types.github import GitHubConfig
from airas.usecases.reproduction import fetch_paper_reproduction_results as module

CONFIG = GitHubConfig(github_owner="acme", repository_name="repro", branch_name="main")
LLM = NodeLLMConfig(llm_name="test-model")
KEYS = {
    "result",
    "validation",
    "parameter_check",
    "final_status",
    "repro_md",
    "repro_png_base64",
}
OUTPUTS: dict[str, Any] = {
    "result": {"summary": "ran fine", "metrics": {"acc": 0.9}},
    "repro_md": "# repro",
    "repro_png_base64": "aGk=",
    "main_py": "print('hi')",
    "run_log": "done",
    "paper_txt": "We report 0.9 accuracy.",
    "paper_extraction": {"parameters": [{"name": "lr", "value": 0.1}]},
    "reproduction_yaml": "lr: 0.1  # source: paper\n",
}


def _outputs(outputs: dict[str, Any]):
    async def fetch(**_: Any) -> dict[str, Any]:
        return outputs

    return fetch


def _judge(severity: str):
    async def judge(**kw: Any) -> dict[str, Any]:
        assert kw["llm_config"] is LLM and kw["paper_text"] == OUTPUTS["paper_txt"]
        assert "- match: lr (source=paper)" in kw["evidence"]
        return {"severity": severity, "reproduction_level": "high", "text": "ok"}

    return judge


async def _run(monkeypatch: pytest.MonkeyPatch, outputs, judge=None) -> dict[str, Any]:
    monkeypatch.setattr(module, "fetch_reproduction_outputs", outputs)
    if judge is not None:
        monkeypatch.setattr(module, "judge_reproduction", judge)
    return await module.fetch_paper_reproduction_results(
        object(), object(), CONFIG, "1706.03762-20260101-000000", LLM
    )


async def test_a_clean_run_passes_with_the_judge_verdict(monkeypatch) -> None:
    out = await _run(monkeypatch, _outputs(OUTPUTS), _judge("ok"))
    assert set(out) == KEYS
    assert out["result"] == OUTPUTS["result"]
    assert (out["repro_md"], out["repro_png_base64"]) == ("# repro", "aGk=")
    assert out["validation"]["severity"] == "ok"
    assert out["parameter_check"]["matched"][0]["name"] == "lr"
    assert out["final_status"] == {
        "status": "passed",
        "validation_severity": "ok",
        "reproduction_level": "high",
    }


async def test_only_critical_fails(monkeypatch) -> None:
    assert (await _run(monkeypatch, _outputs(OUTPUTS), _judge("warning")))[
        "final_status"
    ]["status"] == "passed"
    assert (await _run(monkeypatch, _outputs(OUTPUTS), _judge("critical")))[
        "final_status"
    ]["status"] == "failed"


async def test_a_fetch_failure_is_reported_and_nothing_is_judged(monkeypatch) -> None:
    async def boom(**_: Any) -> dict[str, Any]:
        raise RuntimeError("404 from GitHub")

    async def never(**_: Any) -> dict[str, Any]:
        raise AssertionError("judge must not run")

    out = await _run(monkeypatch, boom, never)
    assert set(out) == KEYS
    assert out["result"] is None and out["validation"] is None
    assert out["final_status"] == {"status": "failed", "fetch_error": "404 from GitHub"}


async def test_a_missing_result_json_fails_before_validation(monkeypatch) -> None:
    out = await _run(monkeypatch, _outputs({**OUTPUTS, "result": None}))
    assert set(out) == KEYS
    assert out["repro_md"] == "# repro"
    assert out["final_status"] == {"status": "failed", "run_error": "result_missing"}


async def test_a_run_that_reported_an_error_is_not_validated(monkeypatch) -> None:
    out = await _run(
        monkeypatch, _outputs({**OUTPUTS, "result": {"error": "gpu_required"}})
    )
    assert out["result"] == {"error": "gpu_required"}
    assert out["validation"] is None and out["parameter_check"] is None
    assert out["final_status"] == {"status": "failed", "run_error": "gpu_required"}


async def test_a_judge_failure_keeps_the_deterministic_checks(monkeypatch) -> None:
    async def boom(**_: Any) -> dict[str, Any]:
        raise ValueError("No response from LLM in judge_reproduction.")

    out = await _run(monkeypatch, _outputs(OUTPUTS), boom)
    assert set(out) == KEYS
    assert out["validation"] is None
    assert out["parameter_check"]["matched"][0]["name"] == "lr"
    assert out["final_status"] == {
        "status": "failed",
        "validation_error": "No response from LLM in judge_reproduction.",
    }


def test_repro_id_is_validated_first() -> None:
    with pytest.raises(ValueError, match="invalid repro_id"):
        module.validate_repro_id("../escape")
