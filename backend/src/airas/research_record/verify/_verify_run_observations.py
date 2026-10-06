from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from airas.core.hashing import text_sha256
from airas.core.research_paths import (
    HOOK_PATH,
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
    if file_bytes_at_commit(root, first, HOOK_PATH) is None:
        return None, [
            f"the repository's first commit has no {HOOK_PATH}: it was not created "
            "from airas-template"
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


def _sections(observed: dict[str, Any], key: str) -> list[dict[str, Any]]:
    if key in observed:
        return [observed[key]]
    return [p[key] for p in observed.get("processes", []) if key in p]


def _loaded_files(observed: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return [
        (module, entry)
        for files in _sections(observed, "loaded_file_hashes")
        for module, entry in files.items()
    ]


def _definition_origins(observed: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (f"{module}.{name}", origin.get("file") or "")
        for tables in _sections(observed, "loaded_definitions")
        for module, table in tables.items()
        for name, origin in table.items()
    ]


def _overrides(observed: dict[str, Any]) -> list[tuple[str, str, list[str]]]:
    return [
        (cls, base, ext.get("overrides", []))
        for extensions in _sections(observed, "upstream_extensions")
        for cls, ext in extensions.items()
        for base in ext.get("bases", [])
    ]


def _calls(observed: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for p in observed.get("processes", []) for c in p.get("calls", [])]


def _cwd(observed: dict[str, Any]) -> str:
    return next(
        (
            p["process"]["cwd"]
            for p in observed.get("processes", [])
            if p.get("process", {}).get("cwd")
        ),
        "",
    )


def _same_value(declared: Any, observed: Any) -> bool | None:
    if not isinstance(observed, dict):
        return bool(observed == declared)

    if "redacted" in observed:
        return None

    text = declared if isinstance(declared, str) else repr(declared)
    if "repr" in observed:
        return bool(observed["repr"] == text)

    return bool(observed.get("sha256") == text_sha256(text))


def _argument_problem(
    label: str, argument: str, value: Any, calls: list[dict[str, Any]]
) -> str | None:
    fn, _, arg = argument.rpartition(".")
    bound = [c.get("args", {}) for c in calls if c.get("fn") == fn]
    if not bound:
        return f"{label}: {fn} (argument {arg}) was never called"

    if any(arg not in args for args in bound):
        return f"{label}: {fn} was called without an argument {arg}"

    other = next(
        (args[arg] for args in bound if _same_value(value, args[arg]) is False),
        None,
    )
    if other is not None:
        return f"{label}: {argument} was {other!r}, not the declared {value!r}"
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
            if changed:
                problems.append(
                    f"{label}: {', '.join(changed)} at commit {result.commit[:12]} differ "
                    "from the repository's first commit"
                )

    package = repository.method_entry.split(".")[0]
    upstream = [
        (m, e) for m, e in _loaded_files(observed) if m.split(".")[0] == package
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

    calls = _calls(observed)
    if not any(c.get("fn") == repository.method_entry for c in calls):
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
        if (problem := _argument_problem(label, argument, value, calls)) is not None
    ]

    # Changes to the upstream: a name defined in src/ or by exec, or a src
    # class overriding the upstream's methods, each needs an extension point.
    points = integration.extension_points
    src = _cwd(observed).rstrip("/") + "/src/"
    problems += [
        f"{label}: upstream {name} is defined in {file}, which no extension_point declares"
        for name, file in _definition_origins(observed)
        if (file.startswith(src) or file.startswith("<")) and not _covered(name, points)
    ]
    problems += [
        f"{label}: {cls} overrides {base}.{', '.join(uncovered)}, which no extension_point declares"
        for cls, base, overrides in _overrides(observed)
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
        snapshot = root / repository_snapshot_relpath(repository.id)
        pages = (
            _pages(snapshot.read_text(encoding="utf-8")) if snapshot.is_file() else {}
        )
        problems += _run_problems(
            root, run, observed, repository, integration, pages, first_commit
        )
    return problems
