"""A realized run's observed.json against its design's repository integration."""

import json
import subprocess
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
ADAPTER_PY = "import pkg\nclass MyModel(pkg.model.Model):\n    def predict(self): ...\n"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _template_import(root: Path) -> str:
    """The repository's first commit, as prepare_repository leaves it: the
    template's hook and Makefile, plus the experiment code. Returns its hash."""
    hook = root / ".airas/sitecustomize.py"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("# hook\n")
    (root / "Makefile").write_text("run:\n\tmake run-experiment\n")
    workflow = root / ".github/workflows/verify_record.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("on: push\n")
    adapter = root / "src/adapter.py"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_text(ADAPTER_PY)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "add", ".airas", ".github", "Makefile", "src")
    _git(root, "commit", "-q", "-m", "Initial commit")
    return _git(root, "rev-parse", "HEAD")


def _record(root: Path, run_commit: str) -> ResearchRecord:
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
                                                commit=run_commit,
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


def _arg(name: str, *values: Any) -> dict[str, Any]:
    """An argument as the hook aggregates it: its name, each value with its count."""
    return {
        "name": name,
        "calls": len(values),
        "values": [{"value": v, "calls": 1} for v in values],
    }


def _observed(root: Path) -> dict[str, Any]:
    return {
        "version": 3,
        "run_id": "run-1",
        "hook": {"sha256": file_sha256(root / ".airas/sitecustomize.py")},
        "src_modules": {"src/adapter.py": text_sha256(ADAPTER_PY)},
        "loaded_file_hashes": {
            "pkg.runner": {
                "file": "/venv/site-packages/pkg/runner.py",
                "sha256": text_sha256(RUNNER_PY),
            }
        },
        "redefinitions": {},
        "extensions": {  # every non-stdlib ancestor, nearest first
            "adapter.MyModel": {
                "bases": ["pkg.model.Model", "pkg.model.Provider"],
                "overrides": ["predict"],
            },
            # a base outside the upstream needs no extension point
            "adapter.Schema": {
                "bases": ["pydantic.main.BaseModel"],
                "overrides": ["model_post_init"],
            },
        },
        "calls": {
            "pkg.runner.Runner.__init__": {
                "calls": 1,
                "args": [_arg("n", 20)],
                "samples": [],
            },
            ENTRY: {"calls": 1, "args": [], "samples": []},
        },
        "processes": [{"pid": 1}],
    }


def _write(root: Path, observed: dict[str, Any]) -> None:
    path = root / ".research/results/run-1/observed.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(observed))


def test_a_run_that_agrees_with_its_declaration_passes(tmp_path: Path) -> None:
    record = _record(tmp_path, _template_import(tmp_path))
    _write(tmp_path, _observed(tmp_path))
    assert verify_run_observations(tmp_path, record) == []


def test_a_realized_run_without_observed_json_fails(tmp_path: Path) -> None:
    record = _record(tmp_path, _template_import(tmp_path))
    assert verify_run_observations(tmp_path, record) == [
        "run 'run-1': no observed.json among its outputs (the Makefile writes it)"
    ]


def test_an_older_hooks_observed_json_is_reported_not_read(tmp_path: Path) -> None:
    record = _record(tmp_path, _template_import(tmp_path))
    _write(tmp_path, {"version": 1, "processes": []})
    problems = verify_run_observations(tmp_path, record)
    assert problems == [
        "run 'run-1': observed.json is version 1, written by an older hook; the "
        "gate reads version 3"
    ]


def _tamper_hook(o: dict[str, Any]) -> None:
    o["hook"]["sha256"] = "0" * 64


def _drop_hashes(o: dict[str, Any]) -> None:
    o["loaded_file_hashes"] = {}


def _modify_upstream(o: dict[str, Any]) -> None:
    o["loaded_file_hashes"]["pkg.runner"]["sha256"] = "0" * 64


def _load_unknown_module(o: dict[str, Any]) -> None:
    o["loaded_file_hashes"]["pkg._version"] = {
        "file": "/venv/pkg/_version.py",
        "sha256": "1" * 64,
    }


def _skip_entry(o: dict[str, Any]) -> None:
    del o["calls"][ENTRY]


def _other_value(o: dict[str, Any]) -> None:
    o["calls"]["pkg.runner.Runner.__init__"]["args"] = [_arg("n", 20, 21)]
    o["calls"]["pkg.runner.Runner.__init__"]["calls"] = 2


def _sometimes_without_the_argument(o: dict[str, Any]) -> None:
    o["calls"]["pkg.runner.Runner.__init__"]["calls"] = 2


def _monkeypatch(o: dict[str, Any]) -> None:
    o["redefinitions"]["pkg.runner.Runner.run"] = "src/adapter.py"


def _redefines_a_dependency(o: dict[str, Any]) -> None:
    o["redefinitions"]["scipy.optimize.least_squares"] = "src/adapter.py"


def _undeclared_base(o: dict[str, Any]) -> None:
    o["extensions"]["adapter.MyModel"]["bases"] = ["pkg.model.Other"]


def _other_src(o: dict[str, Any]) -> None:
    o["src_modules"]["src/adapter.py"] = "0" * 64


def _src_not_in_commit(o: dict[str, Any]) -> None:
    o["src_modules"]["src/extra.py"] = "0" * 64


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            _tamper_hook,
            "was not written by the .airas/sitecustomize.py the repository was created with",
        ),
        (_drop_hashes, "no loaded module of pkg.runner.Runner.run has a file hash"),
        (_modify_upstream, "loaded module pkg.runner differs from the snapshot"),
        (
            _load_unknown_module,
            "loaded module pkg._version (/venv/pkg/_version.py) has no file",
        ),
        (_skip_entry, "method_entry pkg.runner.Runner.run was never called"),
        (_other_value, "pkg.runner.Runner.__init__.n was 21, not the declared 20"),
        (
            _sometimes_without_the_argument,
            "pkg.runner.Runner.__init__ was called without an argument n",
        ),
        (_monkeypatch, "pkg.runner.Runner.run is defined in src/adapter.py"),
        (
            _redefines_a_dependency,
            "scipy.optimize.least_squares is defined in src/adapter.py, which no "
            "extension_point declares",
        ),
        (_undeclared_base, "adapter.MyModel overrides pkg.model.Other.predict"),
        (_other_src, "src/adapter.py that ran differs from commit"),
        (_src_not_in_commit, "src/extra.py ran but commit"),
    ],
)
def test_each_departure_from_the_declaration_is_reported(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], expected: str
) -> None:
    record = _record(tmp_path, _template_import(tmp_path))
    observed = _observed(tmp_path)
    mutate(observed)
    _write(tmp_path, observed)
    problems = verify_run_observations(tmp_path, record)
    assert len(problems) == 1 and expected in problems[0], problems


def test_a_run_from_a_commit_that_edited_the_trusted_files_fails(
    tmp_path: Path,
) -> None:
    """The hook hash can be copied into a forged observed.json; the Makefile
    and hook as they were at the run's commit cannot."""
    _template_import(tmp_path)
    observed = _observed(tmp_path)
    (tmp_path / "Makefile").write_text("run:\n\techo skip\n")
    _git(tmp_path, "commit", "-q", "-am", "skip the hook")
    record = _record(tmp_path, _git(tmp_path, "rev-parse", "HEAD"))
    _write(tmp_path, observed)
    problems = verify_run_observations(tmp_path, record)
    assert len(problems) == 1 and problems[0].startswith(
        "run 'run-1': Makefile at commit "
    ), problems


def test_a_workflow_edited_after_the_import_is_reported(tmp_path: Path) -> None:
    _template_import(tmp_path)
    observed = _observed(tmp_path)
    (tmp_path / ".github/workflows/verify_record.yml").write_text("on: never\n")
    _git(tmp_path, "commit", "-q", "-am", "own gate")
    record = _record(tmp_path, _git(tmp_path, "rev-parse", "HEAD"))
    _write(tmp_path, observed)
    problems = verify_run_observations(tmp_path, record)
    assert len(problems) == 1 and problems[0].startswith(
        "run 'run-1': .github/workflows/verify_record.yml at commit "
    ), problems


def test_a_knob_varied_over_runs_is_read_from_each_runs_params(tmp_path: Path) -> None:
    record = _record(tmp_path, _template_import(tmp_path))
    design = record.hypotheses[0].claims[0].designs[0]
    design.repository_integration.arguments = [
        ArgumentValue(argument="pkg.runner.Runner.__init__.n", params_key="n")
    ]
    design.runs[0].params = {"n": 20}
    _write(tmp_path, _observed(tmp_path))
    assert verify_run_observations(tmp_path, record) == []
    design.runs[0].params = {"n": 7}
    assert verify_run_observations(tmp_path, record) == [
        "run 'run-1': pkg.runner.Runner.__init__.n was 20, not the declared 7"
    ]
    design.runs[0].params = {}
    assert verify_run_observations(tmp_path, record) == [
        "run 'run-1': pkg.runner.Runner.__init__.n reads params['n'], which the run "
        "does not declare"
    ]


def test_a_repository_without_the_template_hook_in_its_first_commit_is_reported(
    tmp_path: Path,
) -> None:
    _template_import(tmp_path)
    observed = _observed(tmp_path)
    _git(tmp_path, "rm", "-q", "--cached", ".airas/sitecustomize.py")
    _git(tmp_path, "commit", "-q", "--amend", "-m", "no hook")
    record = _record(tmp_path, _git(tmp_path, "rev-parse", "HEAD"))
    _write(tmp_path, observed)
    assert verify_run_observations(tmp_path, record) == [
        "the repository's first commit has no .airas/sitecustomize.py: it was not "
        "created from airas-template"
    ]


def test_a_result_commit_git_cannot_show_is_reported_not_passed(tmp_path: Path) -> None:
    _template_import(tmp_path)
    record = _record(tmp_path, "f" * 40)
    _write(tmp_path, _observed(tmp_path))
    problems = verify_run_observations(tmp_path, record)
    assert problems == [
        "run 'run-1': Makefile, .github, .airas at commit ffffffffffff could not be "
        "compared with the repository's first commit",
        "run 'run-1': src/adapter.py ran but commit ffffffffffff has no such file",
    ]


def test_a_history_with_several_roots_cannot_serve_as_the_reference(
    tmp_path: Path,
) -> None:
    first = _template_import(tmp_path)
    branch = _git(tmp_path, "rev-parse", "--abbrev-ref", "HEAD")
    observed = _observed(tmp_path)
    _git(tmp_path, "checkout", "-q", "--orphan", "other")
    (tmp_path / "other.txt").write_text("x\n")
    _git(tmp_path, "add", "other.txt")
    _git(tmp_path, "commit", "-q", "-m", "unrelated root")
    _git(tmp_path, "checkout", "-q", branch)
    _git(tmp_path, "merge", "-q", "--allow-unrelated-histories", "-m", "merge", "other")
    record = _record(tmp_path, first)
    _write(tmp_path, observed)
    problems = verify_run_observations(tmp_path, record)
    assert len(problems) == 1 and "several root commits" in problems[0], problems


def test_a_long_or_structured_value_is_compared_through_its_recording(
    tmp_path: Path,
) -> None:
    record = _record(tmp_path, _template_import(tmp_path))
    record.hypotheses[0].claims[0].designs[0].repository_integration.arguments = [
        ArgumentValue(argument="pkg.runner.Runner.__init__.n", value=[1, 2]),
        ArgumentValue(argument="pkg.runner.Runner.__init__.key", value="k" * 300),
    ]
    observed = _observed(tmp_path)
    observed["calls"]["pkg.runner.Runner.__init__"]["args"] = [
        _arg("n", [1, 2]),  # a small container is kept as a value
        {  # a long string is kept only as its hash
            "name": "key",
            "calls": 1,
            "values": [
                {
                    "truncated": True,
                    "len": 300,
                    "sha256": text_sha256("k" * 300),
                    "calls": 1,
                }
            ],
        },
    ]
    _write(tmp_path, observed)
    assert verify_run_observations(tmp_path, record) == []


def test_a_rerun_is_checked_against_its_own_commit_not_earlier_results(
    tmp_path: Path,
) -> None:
    first = _template_import(tmp_path)
    (tmp_path / "src/adapter.py").write_text(ADAPTER_PY + "# v2\n")
    _git(tmp_path, "commit", "-q", "-am", "edit the adapter")
    record = _record(tmp_path, first)
    run = record.hypotheses[0].claims[0].designs[0].runs[0]
    run.results.append(
        SeyvalResult(
            verifier="seyval",
            id="x2",
            commit=_git(tmp_path, "rev-parse", "HEAD"),
            metrics={"m": 1.0},
        )
    )
    observed = _observed(tmp_path)
    observed["src_modules"]["src/adapter.py"] = text_sha256(ADAPTER_PY + "# v2\n")
    _write(tmp_path, observed)
    assert verify_run_observations(tmp_path, record) == []


def _redacted(o: dict[str, Any]) -> None:
    o["calls"]["pkg.runner.Runner.__init__"]["args"] = [
        {"name": "n", "calls": 1, "values": [{"redacted": "N", "len": 2, "calls": 1}]}
    ]


def _hashed(text: str) -> dict[str, Any]:
    return {
        "truncated": True,
        "len": len(text),
        "sha256": text_sha256(text),
        "calls": 1,
    }


def _other_hash(o: dict[str, Any]) -> None:
    o["calls"]["pkg.runner.Runner.__init__"]["args"] = [
        {"name": "n", "calls": 1, "values": [_hashed("x" * 300)]}
    ]


def _same_json_hash(o: dict[str, Any]) -> None:
    o["calls"]["pkg.runner.Runner.__init__"]["args"] = [
        {"name": "n", "calls": 1, "values": [_hashed('{"a": 2, "b": 1}')]}
    ]


@pytest.mark.parametrize(
    ("declared", "mutate", "expected"),
    [
        (20, _redacted, []),  # a secret cannot be compared, and is not a mismatch
        ("k" * 300, _other_hash, ["was {'truncated': True, 'len': 300"]),
        ({"b": 1, "a": 2}, _same_json_hash, []),  # keys sorted on both sides
    ],
)
def test_a_hashed_or_redacted_value_is_compared_through_its_recording(
    tmp_path: Path,
    declared: Any,
    mutate: Callable[[dict[str, Any]], None],
    expected: list[str],
) -> None:
    record = _record(tmp_path, _template_import(tmp_path))
    record.hypotheses[0].claims[0].designs[0].repository_integration.arguments = [
        ArgumentValue(argument="pkg.runner.Runner.__init__.n", value=declared)
    ]
    observed = _observed(tmp_path)
    mutate(observed)
    _write(tmp_path, observed)
    problems = verify_run_observations(tmp_path, record)
    assert len(problems) == len(expected) and all(
        e in p for e, p in zip(expected, problems, strict=True)
    ), problems
