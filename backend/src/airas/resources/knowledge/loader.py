import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

_KNOWLEDGE_DIR = Path(__file__).parent

_REQUIRED_FIELDS = ("name", "description", "category")


class KnowledgeNote(TypedDict):
    name: str
    description: str
    category: str
    tags: list[str]
    dependent_packages: list[str]
    sources: list[str]
    updated: str
    body: str


class KnowledgeNoteSummary(TypedDict):
    name: str
    description: str
    category: str
    tags: list[str]


def _parse_note(path: Path) -> KnowledgeNote | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        logger.warning("Knowledge note %s has no frontmatter; skipping", path)
        return None
    try:
        _, frontmatter, body = text.split("---", 2)
        meta: dict[str, Any] = yaml.safe_load(frontmatter) or {}
    except (ValueError, yaml.YAMLError) as e:
        logger.warning(
            "Knowledge note %s has invalid frontmatter (%s); skipping", path, e
        )
        return None
    missing = [f for f in _REQUIRED_FIELDS if not meta.get(f)]
    if missing:
        logger.warning(
            "Knowledge note %s is missing required fields %s; skipping", path, missing
        )
        return None
    return KnowledgeNote(
        name=str(meta["name"]),
        description=str(meta["description"]),
        category=str(meta["category"]),
        tags=[str(t) for t in meta.get("tags") or []],
        dependent_packages=[str(p) for p in meta.get("dependent_packages") or []],
        sources=[str(s) for s in meta.get("sources") or []],
        updated=str(meta.get("updated") or ""),
        body=body.strip(),
    )


@lru_cache(maxsize=1)
def _load_all() -> dict[str, KnowledgeNote]:
    notes: dict[str, KnowledgeNote] = {}
    for path in sorted(_KNOWLEDGE_DIR.rglob("*.md")):
        if path.name == "README.md":
            continue
        note = _parse_note(path)
        if note is None:
            continue
        if note["name"] in notes:
            logger.warning(
                "Duplicate knowledge note name %r (%s); keeping the first",
                note["name"],
                path,
            )
            continue
        notes[note["name"]] = note
    return notes


def list_knowledge_notes(category: str | None = None) -> list[KnowledgeNoteSummary]:
    return [
        KnowledgeNoteSummary(
            name=n["name"],
            description=n["description"],
            category=n["category"],
            tags=n["tags"],
        )
        for n in _load_all().values()
        if category is None or n["category"] == category
    ]


def get_knowledge_note(name: str) -> KnowledgeNote | None:
    return _load_all().get(name)


def list_knowledge_categories() -> list[str]:
    return sorted({n["category"] for n in _load_all().values()})
