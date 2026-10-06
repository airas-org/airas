"""A realized run's observed.json against the design's repository
integration: the loaded upstream files are the snapshot's, the method's
entry ran, the declared arguments were bound, and every change to the
upstream is a declared extension point."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from airas.core.hashing import file_sha256
from airas.core.research_paths import (
    PAGE_SEPARATOR,
    RESULTS_DIR,
    repository_snapshot_relpath,
)
from airas.core.types.research_record import (
    Repository,
    RepositoryIntegration,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
)

OBSERVED_FILENAME = "observed.json"
HOOK_PATH = ".airas/sitecustomize.py"


def _pages(text: str) -> dict[str, str]:
    """`==> path <==` pages of a repository snapshot, by path."""
    pages = {}
    for page in text.split(PAGE_SEPARATOR):
        head, _, body = page.partition("\n")
        if head.startswith("==> ") and head.endswith(" <=="):
            pages[head[4:-4]] = body
    return pages


def _sections(observed: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """A section the merge hoisted to the top level when every process agreed,
    else one per process."""
    if key in observed:
        return [observed[key]]
    return [p[key] for p in observed.get("processes", []) if key in p]


def _page_for(pages: dict[str, str], module: str) -> str | None:
    stem = module.replace(".", "/")
    for candidate in (f"{stem}.py", f"{stem}/__init__.py"):
        for path, body in pages.items():
            if path == candidate or path.endswith("/" + candidate):
                return body
    return None


def _same_value(declared: Any, observed: Any) -> bool | None:
    """Compare a declared value with how the hook recorded the bound argument
    (plain, or {type, repr} / {type, len, sha256} for long values). None when
    the observation was redacted and cannot be compared."""
    if not isinstance(observed, dict):
        return bool(observed == declared)
    if "redacted" in observed:
        return None
    text = declared if isinstance(declared, str) else repr(declared)
    if "repr" in observed:
        return bool(observed["repr"] == text)
    return bool(observed.get("sha256") == hashlib.sha256(text.encode()).hexdigest())


def _covered(name: str, extension_points: list[str]) -> bool:
    """`pkg.Class.method` is covered by itself or by `pkg.Class`."""
    return name in extension_points or name.rsplit(".", 1)[0] in extension_points


def _run_problems(
    root: Path,
    run_id: str,
    observed: dict[str, Any],
    repository: Repository,
    integration: RepositoryIntegration,
    pages: dict[str, str],
) -> list[str]:
    label = f"run '{run_id}'"
    problems: list[str] = []
    hook = root / HOOK_PATH
    if not hook.is_file() or observed.get("hook", {}).get("sha256") != file_sha256(
        hook
    ):
        problems.append(
            f"{label}: observed.json was not written by this repository's {HOOK_PATH}"
        )

    package = repository.method_entry.split(".")[0]
    for files in _sections(observed, "loaded_file_hashes"):
        for module, entry in files.items():
            if module.split(".")[0] != package:
                continue
            body = _page_for(pages, module)
            if body is None:
                problems.append(
                    f"{label}: loaded module {module} ({entry.get('file')}) has no file "
                    f"in the snapshot of {repository.id} — generated at build, or the "
                    "snapshot's files were too narrow"
                )
            elif hashlib.sha256(body.encode()).hexdigest() != entry.get("sha256"):
                problems.append(
                    f"{label}: loaded module {module} differs from the snapshot of "
                    f"{repository.id} — the upstream was modified"
                )

    calls = [c for p in observed.get("processes", []) for c in p.get("calls", [])]
    if not any(c.get("fn") == repository.method_entry for c in calls):
        problems.append(
            f"{label}: method_entry {repository.method_entry} was never called"
        )
    for setting in integration.arguments:
        fn, _, arg = setting.argument.rpartition(".")
        bound = [c.get("args", {}) for c in calls if c.get("fn") == fn]
        if not bound:
            problems.append(f"{label}: {fn} (argument {arg}) was never called")
            continue
        for args in bound:
            if arg not in args:
                problems.append(f"{label}: {fn} was called without an argument {arg}")
                break
            if _same_value(setting.value, args[arg]) is False:
                problems.append(
                    f"{label}: {setting.argument} was {args[arg]!r}, not the declared "
                    f"{setting.value!r}"
                )
                break

    # Changes to the upstream: a name defined in src/ or by exec, or a
    # subclass overriding the upstream's methods, each needs an extension point.
    cwd = next(
        (
            p["process"]["cwd"]
            for p in observed.get("processes", [])
            if p.get("process", {}).get("cwd")
        ),
        "",
    )
    src = cwd.rstrip("/") + "/src/"
    for definitions in _sections(observed, "loaded_definitions"):
        for module, table in definitions.items():
            for name, origin in table.items():
                file = origin.get("file") or ""
                if (file.startswith(src) or file.startswith("<")) and not _covered(
                    f"{module}.{name}", integration.extension_points
                ):
                    problems.append(
                        f"{label}: upstream {module}.{name} is defined in {file}, "
                        "which no extension_point declares"
                    )
    for extensions in _sections(observed, "upstream_extensions"):
        for cls, ext in extensions.items():
            for base in ext.get("bases", []):
                uncovered = [
                    m
                    for m in ext.get("overrides", [])
                    if not _covered(f"{base}.{m}", integration.extension_points)
                ]
                if base not in integration.extension_points and uncovered:
                    problems.append(
                        f"{label}: {cls} overrides {base}.{', '.join(uncovered)}, "
                        "which no extension_point declares"
                    )
    return problems


def verify_run_observations(root: Path, record: ResearchRecord) -> list[str]:
    """Every realized run of a design that runs a source's code left an
    observed.json, and it agrees with the declaration."""
    repositories = {r.id: r for s in record.active_literature() for r in s.repositories}
    problems: list[str] = []
    for _, claim, design, run in record.active_runs():
        if not (isinstance(claim, SeyvalClaim) and isinstance(design, SeyvalDesign)):
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
        observed = json.loads(observed_path.read_text(encoding="utf-8"))
        snapshot = root / repository_snapshot_relpath(repository.id)
        pages = (
            _pages(snapshot.read_text(encoding="utf-8")) if snapshot.is_file() else {}
        )
        problems += _run_problems(
            root, run.run_id, observed, repository, integration, pages
        )
    return problems
