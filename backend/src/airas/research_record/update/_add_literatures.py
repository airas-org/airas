from pathlib import Path

from airas.core.research_paths import FULLTEXT_FILENAME, PAGE_SEPARATOR, SOURCES_DIR
from airas.core.types.literature_material import LiteratureMaterial
from airas.core.types.research_record import InputRef, LiteratureSource, ResearchRecord
from airas.research_record.read.read_run_outputs import file_sha256
from airas.research_record.render.render_references_bib import unique_bibkey


def _next_source_id(record: ResearchRecord) -> str:
    return f"s{max((int(s.id[1:]) for s in record.literature), default=0) + 1}"


def _write_fulltext(root: Path, source_id: str, pages: list[str]) -> InputRef:
    relpath = f"{SOURCES_DIR}/{source_id}/{FULLTEXT_FILENAME}"
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() for p in (path, *path.parents[:2])) or not (
        path.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError(f"{relpath} is a symlink or leaves the repository")
    path.write_text(PAGE_SEPARATOR.join(pages), encoding="utf-8")
    return InputRef(path=relpath, sha256=file_sha256(path))


def _existing(record: ResearchRecord, m: LiteratureMaterial) -> LiteratureSource | None:
    for s in record.active_literature():
        if m.kind != "paper":
            if s.kind == m.kind and s.url == m.url and s.commit == m.commit:
                return s
        elif (
            (m.doi and s.doi == m.doi)
            or (m.arxiv_id and s.arxiv_id == m.arxiv_id)
            or (m.url and s.url == m.url)
        ):
            return s
    return None


def add_literatures(
    root: Path, record: ResearchRecord, materials: list[LiteratureMaterial]
) -> tuple[list[LiteratureSource], list[str]]:
    """Pin each material as a source, or find it already pinned. Returns the
    sources in the materials' order and the snapshot paths written, so a
    caller can discard them if anything later fails."""
    sources: list[LiteratureSource] = []
    snapshots: list[str] = []
    for m in materials:
        source = _existing(record, m)
        if source is None:
            source_id = _next_source_id(record)
            fulltext = _write_fulltext(root, source_id, m.pages)
            snapshots.append(fulltext.path)
            source = LiteratureSource(
                id=source_id,
                kind=m.kind,
                title=m.title,
                authors=m.authors,
                year=m.year,
                venue=m.venue,
                doi=m.doi,
                arxiv_id=m.arxiv_id,
                url=m.url,
                commit=m.commit,
                bibkey=unique_bibkey(
                    m.bib_title or m.title,
                    m.bib_authors if m.bib_authors is not None else m.authors,
                    m.year,
                    {s.bibkey for s in record.literature},
                ),
                verified_by=m.verified_by,
                verified_at=m.verified_at,
                fulltext=fulltext,
                parser=m.parser,
            )
            record.literature.append(source)
        sources.append(source)
    return sources, snapshots
