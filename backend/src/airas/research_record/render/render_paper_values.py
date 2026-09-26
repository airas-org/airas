from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from airas.core.research_paths import RECORD_PATH
from airas.core.types.map_record_to_publication import PaperValue
from airas.core.types.research_record import ResearchRecord
from airas.infra.local_git import commits_touching, file_bytes_at_commit
from airas.research_record.render._latex_text import AUTO_GENERATED_HEADER, latex_text
from airas.research_record.render._resolve_ref import resolve_ref


def _walk_any(node: Any, path: str) -> Any:
    for segment in path.split(".") if path else []:
        node = node[int(segment)] if isinstance(node, list) else node[segment]
    return node


def _resolve_paper_ref(
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    ref: str,
) -> str:
    head, _, tail = ref.partition(".")

    runs = record.run_index()
    if head in runs and tail.startswith("params."):
        try:
            params = runs[head].params
            if isinstance(params, BaseModel):
                params = params.model_dump()
            node = _walk_any(params, tail[len("params.") :])
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(
                f"'{ref}': run '{head}' declares no such parameter"
            ) from None
        if isinstance(node, bool) or isinstance(node, (dict, list)):
            raise ValueError(f"'{ref}' is not a scalar: {node!r}")
        # Parameters are legitimately strings ("cifar10", "jacob_cov"), so
        # only numbers get rounded; anything else prints as written.
        return f"{node:g}" if isinstance(node, (int, float)) else str(node)

    return f"{resolve_ref(metrics_data, ref):g}"


def _json_lines(node: Any) -> int:
    """Lines `node` takes as record.save writes it (indent=2)."""
    items = list(node.values()) if isinstance(node, dict) else node
    if not isinstance(items, list):
        return 1
    return 2 + sum(_json_lines(item) for item in items) if items else 1


def _record_line(data: Any, ref: str) -> int | None:
    """1-based line of record.json holding `ref`'s number, or None. ponytail:
    counts the layout record.save writes; a hand-formatted record gets no line."""
    run_id, _, tail = ref.partition(".")
    path: list[Any] = []
    live: dict[str, Any] = {}
    for h, hypothesis in enumerate(data.get("hypotheses") or []):
        for c, claim in enumerate(hypothesis.get("claims") or []):
            for d, design in enumerate(claim.get("designs") or []):
                for r, run in enumerate(design.get("runs") or []):
                    if run.get("run_id") == run_id:
                        # last entry for an id is the live one (see `active`)
                        path = ["hypotheses", h, "claims", c, "designs", d, "runs", r]
                        live = run
    if not path:
        return None
    if tail.startswith("params."):
        path += ["params", *tail[len("params.") :].split(".")]
    elif results := live.get("results"):
        path += ["results", len(results) - 1, "metrics", *tail.split(".")]
    else:
        return None
    node, line = data, 1
    try:
        for key in path:
            items = list(node.values()) if isinstance(node, dict) else node
            index = list(node).index(key) if isinstance(node, dict) else int(key)
            line += 1 + sum(_json_lines(item) for item in items[:index])
            node = items[index]
    except (ValueError, IndexError, TypeError):
        return None
    return line


def resolve_paper_values(
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    used_keys: list[str],
    record_json: str | None = None,
) -> tuple[list[PaperValue], list[str]]:
    try:
        data = json.loads(record_json) if record_json else None
    except ValueError:
        data = None
    values: list[PaperValue] = []
    undefined: list[str] = []
    for ref in dict.fromkeys(used_keys):
        try:
            display = _resolve_paper_ref(record, metrics_data, ref)
        except ValueError:
            undefined.append(ref)
            continue
        values.append(
            PaperValue(
                ref=ref,
                display=display,
                derivation=ref,
                line=_record_line(data, ref) if isinstance(data, dict) else None,
            )
        )
    return values, undefined


VALUES_TEX_FILENAME = "values.tex"


def record_link_commit(root: Path) -> str | None:
    commits = commits_touching(root, RECORD_PATH)
    return commits[0] if commits else None


def record_link_json(root: Path, commit: str | None) -> str | None:
    """record.json as the linked commit holds it."""
    data = file_bytes_at_commit(root, commit, RECORD_PATH) if commit else None
    return None if data is None else data.decode("utf-8")


# Characters safe both in a URL and inside \href's first argument (a %
# would comment out the rest of the line, a # would break macro parsing).
_URL_SAFE = re.compile(r"^[A-Za-z0-9:/._~-]+$")


def render_values_tex(
    values: list[PaperValue], repo_url: str | None, ref: str | None = None
) -> str:
    url = f"{repo_url}/blob/{ref}/{RECORD_PATH}" if repo_url and ref else None
    if url and not _URL_SAFE.match(url):
        url = None
    lines = [
        AUTO_GENERATED_HEADER,
        r"\makeatletter",
        r"\newcommand{\airasval}[1]{\@ifundefined{airasval@#1}"
        r"{\airasvalmissing{#1}}{\csname airasval@#1\endcsname}}",
        r"\newcommand{\airasvalmissing}[1]{\textbf{??airasval:\detokenize{#1}??}}",
        r"\providecommand{\unverified}[1]{#1}",
        # \ifdefined at use time: hyperref may load after this file (mdpi
        # loads it at begindocument), and without it the value stays plain.
        # The optional argument is the line anchor; `\#` is # in a hyperref URL.
        (
            rf"\newcommand{{\airasrecordlink}}[2][]{{\ifdefined\href"
            rf"\href{{{url}#1}}{{#2}}\else#2\fi}}"
            if url
            else r"\newcommand{\airasrecordlink}[2][]{#2}"
        ),
    ]
    for value in values:
        if value.derivation:
            lines.append(f"% {value.ref} = {value.derivation}")
        anchor = rf"[\#L{value.line}]" if value.line else ""
        lines.append(
            rf"\expandafter\def\csname airasval@{value.ref}\endcsname"
            rf"{{\airasrecordlink{anchor}{{{latex_text(value.display)}}}}}"
        )
    lines.append(r"\makeatother")
    return "\n".join(lines) + "\n"
