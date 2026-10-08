from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from airas.core.hashing import text_sha256
from airas.core.research_paths import (
    HOOK_PATH,
    MAKEFILE_PATH,
    OBSERVED_FILENAME,
    PAGE_SEPARATOR,
    RESULTS_DIR,
    TRUSTED_PATHS,
    repository_snapshot_relpath,
)
from airas.core.types.research_record import (
    Repository,
    RepositoryIntegration,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalRun,
)
from airas.infra.local_git import (
    file_bytes_at_commit,
    is_shallow,
    paths_changed_between,
    root_commit,
)


def _first_commit(root: Path) -> tuple[str | None, list[str]]:
    """The commit the trusted files are compared with — the template import,
    a repository prepare_repository created starts from — or why there is none."""
    if is_shallow(root) or (first := root_commit(root)) is None:
        return None, [
            f"{', '.join(TRUSTED_PATHS)} could not be compared with the repository's "
            "first commit (shallow clone, no git history, or several root commits) — "
            "CI must check out with fetch-depth: 0"
        ]
    # The import must carry the run path and the gate: the Makefile, the hook, the workflows.
    required = (MAKEFILE_PATH, HOOK_PATH, ".github")
    missing = [p for p in required if file_bytes_at_commit(root, first, p) is None]
    if missing:
        return None, [
            f"the repository's first commit has no {', '.join(missing)}: it was not "
            "created from airas-template"
        ]
    return first, []


def _pages(text: str) -> dict[str, str]:
    """`==> path <==` pages of a repository snapshot, by path."""
    pages = {}
    for page in text.split(PAGE_SEPARATOR):
        head, _, body = page.partition("\n")
        if head.startswith("==> ") and head.endswith(" <=="):
            pages[head[4:-4]] = body
    return pages


def _page_for(pages: dict[str, str], module: str) -> str | None:
    stem = module.replace(".", "/")
    candidates = (f"{stem}.py", f"{stem}/__init__.py")
    return next(
        (
            body
            for path, body in pages.items()
            if any(path == c or path.endswith("/" + c) for c in candidates)
        ),
        None,
    )


def _overrides(
    observed: dict[str, Any], package: str
) -> list[tuple[str, str, list[str]]]:
    """(src class, its nearest upstream base, methods it overrides). The hook
    lists every non-stdlib ancestor; only the upstream's count here, and
    declaring the class one subclasses is enough."""
    found = []
    for cls, ext in observed.get("extensions", {}).items():
        bases = [b for b in ext.get("bases", []) if b.split(".")[0] == package]
        if bases:
            found.append((cls, bases[0], ext.get("overrides", [])))
    return found


def _same_value(declared: Any, item: dict[str, Any]) -> bool | None:
    if "value" in item:
        return bool(item["value"] == declared)
    if "sha256" in item:
        text = (
            declared
            if isinstance(declared, str)
            else json.dumps(declared, ensure_ascii=False, sort_keys=True)
        )
        return bool(item["sha256"] == text_sha256(text))
    return None


def _argument_problem(
    label: str, argument: str, value: Any, bound: dict[str, dict[str, Any]]
) -> str | None:
    fn, _, arg = argument.rpartition(".")
    called = bound.get(fn)
    if called is None:
        return f"{label}: {fn} (argument {arg}) was never called"

    entry = next((a for a in called.get("args", []) if a.get("name") == arg), None)
    if entry is None or entry["calls"] < called["calls"]:
        return f"{label}: {fn} was called without an argument {arg}"

    other = next(
        (e for e in entry.get("values", []) if _same_value(value, e) is False), None
    )
    if other is not None:
        seen = other.get("value", other)
        return f"{label}: {argument} was {seen!r}, not the declared {value!r}"
    return None


def _covered(name: str, extension_points: list[str]) -> bool:
    return name in extension_points or name.rsplit(".", 1)[0] in extension_points


def _run_problems(
    root: Path,
    run: SeyvalRun,
    observed: dict[str, Any],
    repository: Repository,
    integration: RepositoryIntegration,
    pages: dict[str, str],
    first_commit: str | None,
) -> list[str]:
    label = f"run '{run.run_id}'"
    problems: list[str] = []

    if first_commit is not None:
        trusted_hook = file_bytes_at_commit(root, first_commit, HOOK_PATH) or b""
        if (
            observed.get("hook", {}).get("sha256")
            != hashlib.sha256(trusted_hook).hexdigest()
        ):
            problems.append(
                f"{label}: observed.json was not written by the {HOOK_PATH} the repository "
                "was created with"
            )
        for result in run.results:
            if result.commit is None:
                problems.append(
                    f"{label}: result {result.id} names no commit to check "
                    f"{', '.join(TRUSTED_PATHS)} at"
                )
                continue
            changed = paths_changed_between(
                root, first_commit, result.commit, TRUSTED_PATHS
            )
            if changed is None:
                problems.append(
                    f"{label}: {', '.join(TRUSTED_PATHS)} at commit {result.commit[:12]} "
                    "could not be compared with the repository's first commit"
                )
            elif changed:
                problems.append(
                    f"{label}: {', '.join(changed)} at commit {result.commit[:12]} differ "
                    "from the repository's first commit"
                )

    package = repository.method_entry.split(".")[0]
    upstream = [
        (m, e)
        for m, e in observed.get("loaded_file_hashes", {}).items()
        if m.split(".")[0] == package
    ]
    # Without the entry's own module among the hashes, the checks below pass on nothing.
    if not any(repository.method_entry.startswith(m + ".") for m, _ in upstream):
        problems.append(
            f"{label}: no loaded module of {repository.method_entry} has a file hash"
        )
    problems += [
        f"{label}: loaded module {module} ({entry.get('file')}) has no file in the snapshot "
        f"of {repository.id} — generated at build, or the snapshot's files were too narrow"
        for module, entry in upstream
        if _page_for(pages, module) is None
    ]
    problems += [
        f"{label}: loaded module {module} differs from the snapshot of {repository.id} — "
        "the upstream was modified"
        for module, entry in upstream
        if (body := _page_for(pages, module)) is not None
        and text_sha256(body) != entry.get("sha256")
    ]

    bound = observed.get("calls", {})
    if repository.method_entry not in bound:
        problems.append(
            f"{label}: method_entry {repository.method_entry} was never called"
        )
    # A fixed value is declared; a varied one is this run's params entry.
    expected: list[tuple[str, Any]] = []
    for setting in integration.arguments:
        if not setting.params_key:
            expected.append((setting.argument, setting.value))
        elif setting.params_key in run.params:
            expected.append((setting.argument, run.params[setting.params_key]))
        else:
            problems.append(
                f"{label}: {setting.argument} reads params[{setting.params_key!r}], "
                "which the run does not declare"
            )
    problems += [
        problem
        for argument, value in expected
        if (problem := _argument_problem(label, argument, value, bound)) is not None
    ]

    # The experiment code that ran is the code at the latest result's commit:
    # observed.json is the latest run's, earlier results keep their own commits.
    latest = run.latest_result()
    commit = latest.commit if latest is not None else None
    if commit is not None:
        for path, sha in observed.get("src_modules", {}).items():
            data = file_bytes_at_commit(root, commit, path)
            if data is None:
                problems.append(
                    f"{label}: {path} ran but commit {commit[:12]} has no such file"
                )
            elif hashlib.sha256(data).hexdigest() != sha:
                problems.append(
                    f"{label}: {path} that ran differs from commit {commit[:12]}"
                )

    # Changes to the upstream or any dependency: a name redefined from src/ or
    # by exec, or a src class overriding the upstream's methods, each needs an
    # extension point.
    points = integration.extension_points
    problems += [
        f"{label}: {name} is defined in {file}, which no extension_point declares"
        for name, file in observed.get("redefinitions", {}).items()
        if not _covered(name, points)
    ]
    problems += [
        f"{label}: {cls} overrides {base}.{', '.join(uncovered)}, which no extension_point declares"
        for cls, base, overrides in _overrides(observed, package)
        if base not in points
        and (uncovered := [m for m in overrides if not _covered(f"{base}.{m}", points)])
    ]
    return problems


def verify_run_observations(root: Path, record: ResearchRecord) -> list[str]:
    repositories = {r.id: r for s in record.active_literature() for r in s.repositories}
    problems: list[str] = []
    first_commit: str | None = None
    first_checked = False

    for _, claim, design, run in record.active_runs():
        if not (
            isinstance(claim, SeyvalClaim)
            and isinstance(design, SeyvalDesign)
            and isinstance(run, SeyvalRun)
        ):
            continue

        integration = design.repository_integration
        if integration is None or not run.results:
            continue

        repository = repositories.get(integration.repository_id)
        if repository is None:
            continue  # the record's own checks report it

        observed_path = root / RESULTS_DIR / run.run_id / OBSERVED_FILENAME
        if not observed_path.is_file():
            problems.append(
                f"run '{run.run_id}': no {OBSERVED_FILENAME} among its outputs "
                "(the Makefile writes it)"
            )
            continue

        if not first_checked:  # once per repository, only when a run needs it
            first_commit, first_problems = _first_commit(root)
            problems += first_problems
            first_checked = True

        observed = json.loads(observed_path.read_text(encoding="utf-8"))
        if observed.get("version") != 3:
            problems.append(
                f"run '{run.run_id}': {OBSERVED_FILENAME} is version "
                f"{observed.get('version')}, written by an older hook; the gate reads version 3"
            )
            continue
        snapshot = root / repository_snapshot_relpath(repository.id)
        pages = (
            _pages(snapshot.read_text(encoding="utf-8")) if snapshot.is_file() else {}
        )
        problems += _run_problems(
            root, run, observed, repository, integration, pages, first_commit
        )
    return problems
