from __future__ import annotations

import logging
import re

from airas.core.types.research_record import PASSAGE_ID_PATTERN

logger = logging.getLogger(__name__)


def _macro_arguments(line: str, macro: str) -> list[str]:
    """The argument of every `\\<macro>{...}` on the line, braces balanced, so
    `\\unverified{\\texttt{sha}}` is one argument rather than none."""
    token = f"\\{macro}{{"
    arguments: list[str] = []
    start = 0
    while (at := line.find(token, start)) != -1:
        depth, i = 1, at + len(token)
        while i < len(line) and depth:
            depth += {"{": 1, "}": -1}.get(line[i], 0)
            i += 1
        if depth == 0:
            arguments.append(line[at + len(token) : i - 1])
        start = i
    return arguments


def _strip_comment(line: str) -> str:
    # A % starts a comment unless escaped by an odd number of preceding
    # backslashes: \% is a literal percent, \\% is a line break + comment.
    search_from = 0
    while True:
        at = line.find("%", search_from)
        if at == -1:
            return line
        backslashes = 0
        before = at - 1
        while before >= 0 and line[before] == "\\":
            backslashes += 1
            before -= 1
        if backslashes % 2 == 0:
            return line[:at]
        search_from = at + 1


def scan_main_tex(main_tex: str) -> tuple[list[str], list[str]]:
    unverified: list[str] = []
    used_keys: list[str] = []
    for raw_line in main_tex.splitlines():
        line = _strip_comment(raw_line)
        unverified.extend(_macro_arguments(line, "unverified"))
        used_keys.extend(
            key for key in _macro_arguments(line, "airasval") if key not in used_keys
        )
    return unverified, used_keys


_CITE = re.compile(r"\\cite[pt]?\*?(?:\[([^\]]*)\])?\{([^}]*)\}")


def without_comments(main_tex: str) -> str:
    return "\n".join(_strip_comment(line) for line in main_tex.splitlines())


def scan_citations(main_tex: str) -> list[tuple[str | None, list[str]]]:
    """(locator, keys) of every \\cite, comments stripped."""
    # Comments go line by line; the scan runs over the whole text, since a
    # \\cite may span lines.
    text = without_comments(main_tex)
    return [
        (locator.strip() or None, [k.strip() for k in keys.split(",") if k.strip()])
        for locator, keys in _CITE.findall(text)
    ]


def passage_locators(locator: str | None) -> list[str]:
    """The passage ids in a \\cite locator: one, or several of one source
    as `s1.p1, s1.p2`; anything else (a page number) is not a passage."""
    parts = [part.strip() for part in (locator or "").split(",")]
    return [part for part in parts if re.fullmatch(PASSAGE_ID_PATTERN, part)]
