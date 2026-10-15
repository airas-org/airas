import re
from pathlib import Path

from airas.core.hashing import file_sha256
from airas.core.research_paths import (
    PAGE_SEPARATOR,
    SOURCES_DIR,
    fulltext_relpath,
    repository_snapshot_relpath,
)
from airas.core.types.literature_material import (
    LiteratureMaterial,
    RepositoryMaterial,
)
from airas.core.types.research_record import (
    InputRef,
    LiteratureSource,
    Repository,
    ResearchRecord,
)
from airas.research_record.render.render_references_bib import unique_bibkey


def _next_source_id(root: Path, record: ResearchRecord) -> str:
    # fetch_literature.yml が置いた sources/<id>/ は、まだ record に無くても使用済み
    sources_dir = root / SOURCES_DIR
    imported = (
        [p.name for p in sources_dir.iterdir() if re.fullmatch(r"s\d+", p.name)]
        if sources_dir.is_dir()
        else []
    )
    used = [int(i[1:]) for i in [*imported, *(s.id for s in record.literature)]]
    return f"s{max(used, default=0) + 1}"


def _write_pages(root: Path, relpath: str, pages: list[str]) -> InputRef:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() for p in (path, *path.parents[:2])) or not (
        path.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError(f"{relpath} is a symlink or leaves the repository")
    path.write_text(PAGE_SEPARATOR.join(pages), encoding="utf-8")
    return InputRef(path=relpath, sha256=file_sha256(path))


def _snapshot(
    root: Path, relpath: str, pages: list[str], written: list[str]
) -> InputRef:
    """An imported file is kept as fetch_literature.yml wrote it; anything else is written."""
    path = root / relpath
    if path.is_file():
        return InputRef(path=relpath, sha256=file_sha256(path))
    written.append(relpath)
    return _write_pages(root, relpath, pages)


def _same(s: LiteratureSource, m: LiteratureMaterial) -> bool:
    if m.doi or m.arxiv_id:
        return bool(
            (m.doi and s.doi == m.doi) or (m.arxiv_id and s.arxiv_id == m.arxiv_id)
        )
    if (
        m.repositories
    ):  # code-only work: named after, and identified by, its first repository
        return bool(s.repositories) and (
            s.repositories[0].url,
            s.repositories[0].commit,
        ) == (
            m.repositories[0].url,
            m.repositories[0].commit,
        )
    return bool(m.url) and s.url == m.url


def _existing(record: ResearchRecord, m: LiteratureMaterial) -> LiteratureSource | None:
    return next((s for s in record.latest_literature() if _same(s, m)), None)


def _pin_repositories(
    root: Path,
    source_id: str,
    pinned: list[Repository],
    materials: list[RepositoryMaterial],
) -> tuple[list[Repository], list[str]]:
    """Snapshot each repository not pinned yet as the source's next rN."""
    known = {(r.url, r.commit) for r in pinned}
    added: list[Repository] = []
    paths: list[str] = []
    for material in materials:
        if (material.url, material.commit) in known:
            continue
        repository_id = f"{source_id}.r{len(pinned) + len(added) + 1}"
        snapshot = _snapshot(
            root, repository_snapshot_relpath(repository_id), material.pages, paths
        )
        added.append(
            Repository(
                id=repository_id,
                url=material.url,
                commit=material.commit,
                snapshot=snapshot,
                method_entry=material.method_entry,
            )
        )
    return added, paths


def add_literatures(
    root: Path,
    record: ResearchRecord,
    materials: list[tuple[str | None, LiteratureMaterial]],
) -> tuple[list[LiteratureSource], list[str]]:
    """Pin each material as a source, or find it already pinned and add the
    code it ships that is not pinned yet. Returns the sources in the
    materials' order and the snapshot paths written, so a caller can discard
    them if anything later fails. A material comes with the id of the
    .research/sources/<id>/ it was imported into, or None for code with no
    paper, which gets a new id."""
    sources: list[LiteratureSource] = []
    snapshots: list[str] = []
    for imported_id, m in materials:
        source = _existing(record, m)
        if source is None:
            source_id = imported_id or _next_source_id(root, record)
            fulltext = (
                _snapshot(root, fulltext_relpath(source_id), m.pages, snapshots)
                if m.pages
                else None
            )
            repositories, paths = _pin_repositories(root, source_id, [], m.repositories)
            snapshots += paths
            source = LiteratureSource(
                id=source_id,
                title=m.title,
                authors=m.authors,
                year=m.year,
                venue=m.venue,
                doi=m.doi,
                arxiv_id=m.arxiv_id,
                url=m.url,
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
                repositories=repositories,
            )
            record.literature.append(source)
        else:
            added, paths = _pin_repositories(
                root, source.id, source.repositories, m.repositories
            )
            source.repositories.extend(added)
            snapshots += paths
        sources.append(source)
    return sources, snapshots
