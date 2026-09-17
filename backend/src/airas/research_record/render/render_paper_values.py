from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from airas.core.research_paths import RECORD_PATH
from airas.core.types.map_record_to_publication import PaperValue
from airas.core.types.research_record import ResearchRecord
from airas.infra.local_git import commits_touching
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


def resolve_paper_values(
    record: ResearchRecord, metrics_data: dict[str, Any], used_keys: list[str]
) -> tuple[list[PaperValue], list[str]]:
    values: list[PaperValue] = []
    undefined: list[str] = []
    for ref in dict.fromkeys(used_keys):
        try:
            display = _resolve_paper_ref(record, metrics_data, ref)
        except ValueError:
            undefined.append(ref)
            continue
        values.append(PaperValue(ref=ref, display=display, derivation=ref))
    return values, undefined


VALUES_TEX_FILENAME = "values.tex"


def record_link_commit(root: Path) -> str | None:
    commits = commits_touching(root, RECORD_PATH)
    return commits[0] if commits else None


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
        (
            rf"\newcommand{{\airasrecordlink}}[1]{{\ifdefined\href"
            rf"\href{{{url}}}{{#1}}\else#1\fi}}"
            if url
            else r"\newcommand{\airasrecordlink}[1]{#1}"
        ),
    ]
    for value in values:
        if value.derivation:
            lines.append(f"% {value.ref} = {value.derivation}")
        lines.append(
            rf"\expandafter\def\csname airasval@{value.ref}\endcsname"
            rf"{{\airasrecordlink{{{latex_text(value.display)}}}}}"
        )
    lines.append(r"\makeatother")
    return "\n".join(lines) + "\n"
