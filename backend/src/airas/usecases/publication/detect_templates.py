from __future__ import annotations

import logging
from pathlib import Path
from typing import get_args

from airas.core.types.latex import LATEX_TEMPLATE_NAME

logger = logging.getLogger(__name__)


def detect_templates(local_path: str) -> list[str]:
    latex_root = Path(local_path).expanduser().resolve() / ".research" / "latex"
    if not latex_root.is_dir():
        return []
    known = set(get_args(LATEX_TEMPLATE_NAME))
    found = []
    for path in sorted(latex_root.iterdir()):
        if not (path / "main.tex").is_file():
            continue
        if path.name not in known:
            logger.warning(f"Skipping unknown LaTeX template directory: {path.name}")
            continue
        found.append(path.name)
    return found


def paper_directories(local_path: str) -> list[str]:
    # Every directory holding a main.tex, known template or not — so a caller
    # can tell "no paper yet" from "a paper this version cannot verify".
    latex_root = Path(local_path).expanduser().resolve() / ".research" / "latex"
    if not latex_root.is_dir():
        return []
    return sorted(p.name for p in latex_root.iterdir() if (p / "main.tex").is_file())
