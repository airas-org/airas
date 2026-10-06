"""A realized run's observed.json against its design's repository integration."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from airas.core.hashing import file_sha256, text_sha256
from airas.core.types.research_record import (
    ArgumentValue,
    Criterion,
    Hypothesis,
    InputRef,
    LiteratureSource,
    Prediction,
    Repository,
    RepositoryIntegration,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalResult,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.research_record.verify._verify_run_observations import (
    verify_run_observations,
)

ENTRY = "pkg.runner.Runner.run"
RUNNER_PY = "class Runner:\n    def __init__(self, n=5): ...\n    def run(self): ...\n"
SNAPSHOT = f"==> pkg/runner.py <==\n{RUNNER_PY}"


def _record(root: Path) -> ResearchRecord:
    snapshot = root / ".research/sources/s1/r1.txt"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(SNAPSHOT)
    return ResearchRecord(
        literature=[
            LiteratureSource(
                id="s1",
                title="acme/pkg",
                bibkey="acme-2026-pkg",
                verified_by="git",
                repositories=[
                    Repository(
                        id="s1.r1",
                        url="https://github.com/acme/pkg",
                        commit="a" * 40,
                        snapshot=InputRef(
                            path=".research/sources/s1/r1.txt",
                            sha256=file_sha256(snapshot),
                        ),
                        method_entry=ENTRY,
                    )
                ],
            )
        ],
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="h",
                claims=[
                    SeyvalClaim(
                        verifier=SeyvalVerifier(kind=VerifierKind.SEYVAL),
                        id="c1",
                        statement="s",
                        rationale="r",
                        criterion=Criterion(
                            metric="m", subject="run-1", reference=0.0, op=">="
                        ),
                        prediction=Prediction(low=0.0, high=1.0, basis="b"),
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                repository_integration=RepositoryIntegration(
                                    repository_id="s1.r1",
                                    extension_points=["pkg.model.Model"],
                                    arguments=[
                                        ArgumentValue(
                                            argument="pkg.runner.Runner.__init__.n",
                                            value=20,
                                        )
                                    ],
                                ),
                                runs=[
                                    SeyvalRun(
                                        run_id="run-1",
                                        results=[
                                            SeyvalResult(
                                                verifier="seyval",
                                                id="x1",
                                                commit="c" * 40,
                                                metrics={"m": 1.0},
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


def _observed(root: Path) -> dict[str, Any]:
    hook = root / ".airas/sitecustomize.py"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("# hook\n")
    return {
        "version": 1,
        "run_id": "run-1",
        "hook": {"sha256": file_sha256(hook)},
        "loaded_file_hashes": {
            "pkg.runner": {
                "file": "/venv/site-packages/pkg/runner.py",
                "sha256": text_sha256(RUNNER_PY),
            }
        },
        "loaded_definitions": {
            "pkg.runner": {
                "Runner": {"module": "pkg.runner"},
                "Runner.run": {
                    "module": "pkg.runner",
                    "file": "/venv/site-packages/pkg/runner.py",
                },
            }
        },
        "upstream_extensions": {
            "adapter.MyModel": {"bases": ["pkg.model.Model"], "overrides": ["predict"]}
        },
        "processes": [
            {
                "process": {"pid": 1, "cwd": "/repo"},
                "calls": [
                    {"seq": 0, "fn": "pkg.runner.Runner.__init__", "args": {"n": 20}},
                    {"seq": 1, "fn": ENTRY, "args": {}},
                ],
            }
        ],
    }


def _write(root: Path, observed: dict[str, Any]) -> None:
    path = root / ".research/results/run-1/observed.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(observed))


def test_a_run_that_agrees_with_its_declaration_passes(tmp_path: Path) -> None:
    record = _record(tmp_path)
    _write(tmp_path, _observed(tmp_path))
    assert verify_run_observations(tmp_path, record) == []


def test_a_realized_run_without_observed_json_fails(tmp_path: Path) -> None:
    record = _record(tmp_path)
    _observed(tmp_path)
    assert verify_run_observations(tmp_path, record) == [
        "run 'run-1': no observed.json among its outputs (the Makefile writes it)"
    ]


def _tamper_hook(o: dict[str, Any]) -> None:
    o["hook"]["sha256"] = "0" * 64


def _modify_upstream(o: dict[str, Any]) -> None:
    o["loaded_file_hashes"]["pkg.runner"]["sha256"] = "0" * 64


def _load_unknown_module(o: dict[str, Any]) -> None:
    o["loaded_file_hashes"]["pkg._version"] = {
        "file": "/venv/pkg/_version.py",
        "sha256": "1" * 64,
    }


def _skip_entry(o: dict[str, Any]) -> None:
    o["processes"][0]["calls"].pop()


def _other_value(o: dict[str, Any]) -> None:
    o["processes"][0]["calls"][0]["args"]["n"] = 21


def _monkeypatch(o: dict[str, Any]) -> None:
    o["loaded_definitions"]["pkg.runner"]["Runner.run"] = {
        "module": "adapter",
        "file": "/repo/src/adapter.py",
    }


def _undeclared_base(o: dict[str, Any]) -> None:
    o["upstream_extensions"]["adapter.MyModel"]["bases"] = ["pkg.model.Other"]


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (_tamper_hook, "was not written by this repository's .airas/sitecustomize.py"),
        (_modify_upstream, "loaded module pkg.runner differs from the snapshot"),
        (
            _load_unknown_module,
            "loaded module pkg._version (/venv/pkg/_version.py) has no file",
        ),
        (_skip_entry, "method_entry pkg.runner.Runner.run was never called"),
        (_other_value, "pkg.runner.Runner.__init__.n was 21, not the declared 20"),
        (_monkeypatch, "pkg.runner.Runner.run is defined in /repo/src/adapter.py"),
        (_undeclared_base, "adapter.MyModel overrides pkg.model.Other.predict"),
    ],
)
def test_each_departure_from_the_declaration_is_reported(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], expected: str
) -> None:
    record = _record(tmp_path)
    observed = _observed(tmp_path)
    mutate(observed)
    _write(tmp_path, observed)
    problems = verify_run_observations(tmp_path, record)
    assert len(problems) == 1 and expected in problems[0], problems


def test_a_long_or_structured_value_is_compared_through_its_recording(
    tmp_path: Path,
) -> None:
    record = _record(tmp_path)
    record.hypotheses[0].claims[0].designs[0].repository_integration.arguments = [
        ArgumentValue(argument="pkg.runner.Runner.__init__.n", value=[1, 2]),
        ArgumentValue(argument="pkg.runner.Runner.__init__.key", value="k" * 300),
    ]
    observed = _observed(tmp_path)
    observed["processes"][0]["calls"][0]["args"] = {
        "n": {"type": "list", "repr": "[1, 2]"},
        "key": {"type": "str", "len": 300, "sha256": text_sha256("k" * 300)},
    }
    _write(tmp_path, observed)
    assert verify_run_observations(tmp_path, record) == []
