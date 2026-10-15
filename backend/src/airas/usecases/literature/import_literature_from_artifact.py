import json
import re
from pathlib import Path

from airas.core.research_paths import (
    SOURCE_METADATA_FILENAME,
    SOURCES_DIR,
    SOURCES_PROVENANCE_PATH,
    repo_root,
)
from airas.core.types.imported_source import SOURCES_PROVENANCE, ImportedSource


def import_literature_from_artifact(
    local_path: str, artifact_dir: Path, workflow_run_id: str
) -> dict[str, str]:
    """Each `artifact_dir/<k>/` byte for byte into a new `.research/sources/<id>/`,
    and `.research/sources/.provenance.json` saying which run and entry it is.
    Returns source id -> title."""
    root = repo_root(local_path)
    sources_dir = root / SOURCES_DIR
    provenance_path = root / SOURCES_PROVENANCE_PATH
    provenance = (
        SOURCES_PROVENANCE.validate_json(provenance_path.read_bytes())
        if provenance_path.is_file()
        else {}
    )
    existing = (
        [
            int(p.name[1:])
            for p in sources_dir.iterdir()
            if re.fullmatch(r"s\d+", p.name)
        ]
        if sources_dir.is_dir()
        else []
    )
    next_number = max(existing, default=0) + 1

    imported: dict[str, str] = {}
    entries = sorted(
        (p for p in artifact_dir.iterdir() if p.is_dir()), key=lambda p: int(p.name)
    )
    for entry_dir in entries:
        source_id = f"s{next_number}"
        next_number += 1
        target = sources_dir / source_id
        target.mkdir(parents=True)
        for file in sorted(entry_dir.iterdir()):
            (target / file.name).write_bytes(file.read_bytes())

        provenance[source_id] = ImportedSource(
            workflow_run_id=workflow_run_id, entry=entry_dir.name
        )
        metadata = json.loads(
            (entry_dir / SOURCE_METADATA_FILENAME).read_text(encoding="utf-8")
        )
        imported[source_id] = metadata["title"]

    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(
        SOURCES_PROVENANCE.dump_json(provenance, indent=2).decode() + "\n",
        encoding="utf-8",
    )
    return imported
