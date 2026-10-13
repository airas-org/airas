from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from airas.core.hashing import text_sha256
from airas.core.research_paths import (
    HOOK_PATH,
    MAKEFILE_PATH,
    OBSERVED_FILENAME,
    PAGE_SEPARATOR,
    RECORD_PATH,
    RESULTS_DIR,
    TRUSTED_PATHS,
    repository_snapshot_relpath,
)
from airas.core.types.record_verification import RecordVerification
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


def _first_commit(root: Path, verification: RecordVerification) -> str | None:
    """The commit the trusted files are compared with — the template import,
    a repository prepare_repository created starts from — or None, reported."""
    if is_shallow(root) or (first := root_commit(root)) is None:
        verification.append_declaration_status(
            RECORD_PATH,
            f"{', '.join(TRUSTED_PATHS)} could not be compared with the repository's "
            "first commit (shallow clone, no git history, or several root commits) — "
            "CI must check out with fetch-depth: 0",
            "mismatch",
            evidence_path=MAKEFILE_PATH,
        )
        return None
    # The import must carry the run path and the gate: the Makefile, the hook, the workflows.
    required = (MAKEFILE_PATH, HOOK_PATH, ".github")
    missing = [p for p in required if file_bytes_at_commit(root, first, p) is None]
    if missing:
        verification.append_declaration_status(
            RECORD_PATH,
            f"the repository's first commit has no {', '.join(missing)}: it was not "
            "created from airas-template",
            "mismatch",
            evidence_path=MAKEFILE_PATH,
        )
        return None
    return first


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


def _argument_status(
    label: str, argument: str, value: Any, bound: dict[str, dict[str, Any]]
) -> tuple[str, Literal["verified", "mismatch", "unverified"]]:
    fn, _, arg = argument.rpartition(".")
    called = bound.get(fn)
    if called is None:
        return f"{label}: {fn} (argument {arg}) was never called", "mismatch"

    entry = next((a for a in called.get("args", []) if a.get("name") == arg), None)
    if entry is None or entry["calls"] < called["calls"]:
        return f"{label}: {fn} was called without an argument {arg}", "mismatch"

    comparisons = {id(e): _same_value(value, e) for e in entry.get("values", [])}
    other = next(
        (e for e in entry.get("values", []) if comparisons[id(e)] is False), None
    )
    if other is not None:
        seen = other.get("value", other)
        return (
            f"{label}: {argument} was {seen!r}, not the declared {value!r}",
            "mismatch",
        )
    if all(same is None for same in comparisons.values()):
        return (
            f"{label}: {argument} is recorded redacted and cannot be compared",
            "unverified",
        )
    seen_values = [e.get("value", e.get("sha256", "redacted")) for e in entry["values"]]
    return (
        f"observed {argument} = {seen_values!r} over {called['calls']} calls in {label}",
        "verified",
    )


def _covered(name: str, extension_points: list[str]) -> bool:
    return name in extension_points or name.rsplit(".", 1)[0] in extension_points


def _append_run_statuses(
    root: Path,
    run: SeyvalRun,
    observed: dict[str, Any],
    repository: Repository,
    integration: RepositoryIntegration,
    pages: dict[str, str],
    first_commit: str | None,
    run_path: str,
    design_path: str,
    observed_relpath: str,
    verification: RecordVerification,
) -> None:
    label = f"run '{run.run_id}'"
    repository_path = (
        f"literature[{repository.id.split('.')[0]}]/repositories[{repository.id}]"
    )
    trusted = ", ".join(TRUSTED_PATHS)

    # The hook and the trusted files are about observed.json itself, not a
    # declaration: on a result's path an ok here would cover its leaves.
    if first_commit is None:
        verification.append_declaration_status(
            observed_relpath,
            "first commit unavailable: hook and trusted files unchecked",
            "unverified",
            evidence_path=MAKEFILE_PATH,
        )
    else:
        trusted_hook = file_bytes_at_commit(root, first_commit, HOOK_PATH) or b""
        hook_ok = (
            observed.get("hook", {}).get("sha256")
            == hashlib.sha256(trusted_hook).hexdigest()
        )
        verification.append_declaration_status(
            observed_relpath,
            f"observed.json hook sha256 vs {HOOK_PATH} at the first commit"
            if hook_ok
            else f"{label}: observed.json was not written by the {HOOK_PATH} the "
            "repository was created with",
            "verified" if hook_ok else "mismatch",
            evidence_path=HOOK_PATH,
        )
        for result in run.results:
            result_path = f"{run_path}/results[{result.id}]/commit"
            if result.commit is None:
                verification.append_declaration_status(
                    result_path,
                    f"{label}: result {result.id} names no commit to check {trusted} at",
                    "mismatch",
                    evidence_path=MAKEFILE_PATH,
                )
                continue
            changed = paths_changed_between(
                root, first_commit, result.commit, TRUSTED_PATHS
            )
            if changed is None:
                verification.append_declaration_status(
                    result_path,
                    f"{label}: {trusted} at commit {result.commit[:12]} "
                    "could not be compared with the repository's first commit",
                    "mismatch",
                    evidence_path=MAKEFILE_PATH,
                )
                continue
            verification.append_declaration_status(
                result_path,
                f"{trusted} at this commit vs the first commit"
                if not changed
                else f"{label}: {', '.join(changed)} at commit {result.commit[:12]} "
                "differ from the repository's first commit",
                "mismatch" if changed else "verified",
                evidence_path=MAKEFILE_PATH,
            )

    package = repository.method_entry.split(".")[0]
    upstream = [
        (m, e)
        for m, e in observed.get("loaded_file_hashes", {}).items()
        if m.split(".")[0] == package
    ]
    # Without the entry's own module among the hashes, the checks below pass on nothing.
    entry_hashed = any(repository.method_entry.startswith(m + ".") for m, _ in upstream)
    verification.append_declaration_status(
        f"{repository_path}/method_entry",
        "observed loaded_file_hashes of its module"
        if entry_hashed
        else f"{label}: no loaded module of {repository.method_entry} has a file hash",
        "verified" if entry_hashed else "mismatch",
        evidence_path=observed_relpath,
    )
    snapshot_problems = [
        f"{label}: loaded module {module} ({entry.get('file')}) has no file in the snapshot "
        f"of {repository.id} — generated at build, or the snapshot's files were too narrow"
        for module, entry in upstream
        if _page_for(pages, module) is None
    ]
    snapshot_problems += [
        f"{label}: loaded module {module} differs from the snapshot of {repository.id} — "
        "the upstream was modified"
        for module, entry in upstream
        if (body := _page_for(pages, module)) is not None
        and text_sha256(body) != entry.get("sha256")
    ]
    for problem in snapshot_problems:
        verification.append_declaration_status(
            f"{repository_path}/snapshot",
            problem,
            "mismatch",
            evidence_path=repository_snapshot_relpath(repository.id),
        )
    if not snapshot_problems:
        verification.append_declaration_status(
            f"{repository_path}/snapshot",
            f"observed loaded_file_hashes of {len(upstream)} {package} modules in {label}",
            "verified",
            evidence_path=repository_snapshot_relpath(repository.id),
        )

    bound = observed.get("calls", {})
    entry_called = repository.method_entry in bound
    verification.append_declaration_status(
        f"{repository_path}/method_entry",
        f"observed calls in {label}: {bound[repository.method_entry]['calls']} calls"
        if entry_called
        else f"{label}: method_entry {repository.method_entry} was never called",
        "verified" if entry_called else "mismatch",
        evidence_path=observed_relpath,
    )
    # A fixed value is declared; a varied one is this run's params entry. The
    # row sits on the leaf compared, so the argument's reason stays unchecked.
    for setting in integration.arguments:
        argument_path = (
            f"{design_path}/repository_integration/arguments[{setting.argument}]/"
            + ("params_key" if setting.params_key else "value")
        )
        if not setting.params_key:
            value = setting.value
        elif setting.params_key in run.params:
            value = run.params[setting.params_key]
        else:
            verification.append_declaration_status(
                argument_path,
                f"{label}: {setting.argument} reads params[{setting.params_key!r}], "
                "which the run does not declare",
                "mismatch",
                evidence_path=observed_relpath,
            )
            continue
        reason, status = _argument_status(label, setting.argument, value, bound)
        verification.append_declaration_status(
            argument_path, reason, status, evidence_path=observed_relpath
        )

    # The experiment code that ran is the code at the latest result's commit:
    # observed.json is the latest run's, earlier results keep their own commits.
    latest = run.results[-1]
    if latest.commit is not None:
        src_problems = []
        for path, sha in observed.get("src_modules", {}).items():
            data = file_bytes_at_commit(root, latest.commit, path)
            if data is None:
                src_problems.append(
                    f"{label}: {path} ran but commit {latest.commit[:12]} has no such file"
                )
            elif hashlib.sha256(data).hexdigest() != sha:
                src_problems.append(
                    f"{label}: {path} that ran differs from commit {latest.commit[:12]}"
                )
        src_path = f"{run_path}/results[{latest.id}]/commit"
        for problem in src_problems:
            verification.append_declaration_status(
                src_path, problem, "mismatch", evidence_path=observed_relpath
            )
        if not src_problems:
            verification.append_declaration_status(
                src_path,
                f"observed src_modules sha256 of {len(observed.get('src_modules', {}))} "
                "files vs this commit",
                "verified",
                evidence_path=observed_relpath,
            )

    # Changes to the upstream or any dependency: a name redefined from src/ or
    # by exec, or a src class overriding the upstream's methods, each needs an
    # extension point; a declared point nothing used stays unverified.
    points = integration.extension_points
    extension_points_path = f"{design_path}/repository_integration/extension_points"
    redefinitions = observed.get("redefinitions", {})
    overrides = _overrides(observed, package)
    for name, file in redefinitions.items():
        if not _covered(name, points):
            verification.append_declaration_status(
                extension_points_path,
                f"{label}: {name} is defined in {file}, which no extension_point declares",
                "mismatch",
                evidence_path=observed_relpath,
            )
    for cls, base, methods in overrides:
        uncovered = [m for m in methods if not _covered(f"{base}.{m}", points)]
        if base not in points and uncovered:
            verification.append_declaration_status(
                extension_points_path,
                f"{label}: {cls} overrides {base}.{', '.join(uncovered)}, "
                "which no extension_point declares",
                "mismatch",
                evidence_path=observed_relpath,
            )
    for point in points:
        used = any(_covered(name, [point]) for name in redefinitions) or any(
            base == point or any(_covered(f"{base}.{m}", [point]) for m in methods)
            for _, base, methods in overrides
        )
        verification.append_declaration_status(
            extension_points_path,
            f"{point}: observed as a redefinition or an override in {label}"
            if used
            else f"{point}: declared, but nothing in {label} redefined or overrode it",
            "verified" if used else "unverified",
            evidence_path=observed_relpath,
        )


def verify_run_observations(
    root: Path, record: ResearchRecord, verification: RecordVerification
) -> None:
    repositories = {r.id: r for s in record.latest_literature() for r in s.repositories}
    first_commit: str | None = None
    first_checked = False

    for hypothesis, claim, design, run in record.latest_runs():
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

        design_path = (
            f"hypotheses[{hypothesis.id}]/claims[{claim.id}]/designs[{design.id}]"
        )
        run_path = f"{design_path}/runs[{run.run_id}]"
        observed_relpath = f"{RESULTS_DIR}/{run.run_id}/{OBSERVED_FILENAME}"
        observed_path = root / observed_relpath
        if not observed_path.is_file():
            verification.append_declaration_status(
                observed_relpath,
                f"run '{run.run_id}': no {OBSERVED_FILENAME} among its outputs "
                "(the Makefile writes it)",
                "mismatch",
                evidence_path=MAKEFILE_PATH,
            )
            continue

        if not first_checked:  # once per repository, only when a run needs it
            first_commit = _first_commit(root, verification)
            first_checked = True

        observed = json.loads(observed_path.read_text(encoding="utf-8"))
        if observed.get("version") != 3:
            verification.append_declaration_status(
                observed_relpath,
                f"run '{run.run_id}': {OBSERVED_FILENAME} is version "
                f"{observed.get('version')}, written by an older hook; the gate reads version 3",
                "mismatch",
                evidence_path=HOOK_PATH,
            )
            continue
        snapshot = root / repository_snapshot_relpath(repository.id)
        pages = (
            _pages(snapshot.read_text(encoding="utf-8")) if snapshot.is_file() else {}
        )
        _append_run_statuses(
            root,
            run,
            observed,
            repository,
            integration,
            pages,
            first_commit,
            run_path,
            design_path,
            observed_relpath,
            verification,
        )
