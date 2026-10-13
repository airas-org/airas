from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from airas.core.research_paths import RECORD_PATH, VERIFICATION_MD_PATH
from airas.core.types.record_verification import DeclarationStatus, RecordVerification
from airas.infra.local_git import head_commit, normalize_git_url, remote_origin_url
from airas.research_record.read.declaration_paths import record_json_line


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _table(
    rows: list[DeclarationStatus], record: dict[str, Any], repo_url: str, commit: str
) -> str:
    if not rows:
        return "_なし_\n"
    lines = ["| status | path | reason | links |", "| --- | --- | --- | --- |"]
    for row in rows:
        links = []
        if repo_url and commit:
            line = record_json_line(record, row.path)
            if line is not None:
                links.append(
                    f"[record.json#L{line}]({repo_url}/blob/{commit}/{RECORD_PATH}#L{line})"
                )
            if row.evidence_path:
                links.append(
                    f"[{row.evidence_path}]({repo_url}/blob/{commit}/{row.evidence_path})"
                )
        elif row.evidence_path:
            links.append(row.evidence_path)
        lines.append(
            f"| {row.status} | `{_cell(row.path)}` | {_cell(row.reason)} | {' '.join(links)} |"
        )
    return "\n".join(lines) + "\n"


def _details(summary: str, body: str) -> str:
    return f"<details><summary>{summary}</summary>\n\n{body}\n</details>\n"


def render_verification_md(
    verification: RecordVerification,
    record: dict[str, Any],
    repo_url: str = "",
    commit: str = "",
) -> str:
    by_status = {
        status: [r for r in verification.declaration_statuses if r.status == status]
        for status in ("mismatch", "unverified", "verified")
    }
    return "\n".join(
        [
            "# verify-record",
            "",
            f"- commit: `{commit or '(working tree)'}`",
            f"- stage: {verification.stage}",
            f"- ok: {'yes' if verification.ok else 'no'}",
            f"- rows: {len(verification.declaration_statuses)} = "
            + " / ".join(f"{k} {len(v)}" for k, v in by_status.items()),
            "",
            "## mismatch（problems）",
            "",
            _table(by_status["mismatch"], record, repo_url, commit),
            "## unverified（比べていない: 人間と judge が読む）",
            "",
            _table(by_status["unverified"], record, repo_url, commit),
            _details(
                f"verified（{len(by_status['verified'])} 行）",
                _table(by_status["verified"], record, repo_url, commit),
            ),
        ]
    )


def write_verification_md(root: Path, verification: RecordVerification) -> str:
    """Write the report next to the record, linked to the commit at HEAD."""
    try:
        record = json.loads((root / RECORD_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        record = {}  # the verification itself reports the unreadable record
    markdown = render_verification_md(
        verification,
        record,
        normalize_git_url(remote_origin_url(root) or ""),
        head_commit(root) or "",
    )
    (root / VERIFICATION_MD_PATH).write_text(markdown, encoding="utf-8")
    return markdown
