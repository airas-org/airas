"""import-literature-from-artifact copies each artifact entry byte for byte into
the next free .research/sources/<id>/ and records which run and entry it is."""

import json
from pathlib import Path

from airas.core.types.imported_source import SOURCES_PROVENANCE
from airas.usecases.literature.import_literature_from_artifact import (
    import_literature_from_artifact,
)


def _artifact(tmp_path: Path, titles: list[str]) -> Path:
    artifact = tmp_path / "literature"
    for k, title in enumerate(titles):
        (artifact / str(k)).mkdir(parents=True)
        (artifact / str(k) / "metadata.json").write_text(json.dumps({"title": title}))
        (artifact / str(k) / "fulltext.txt").write_bytes(f"text of {title}\f".encode())
    return artifact


def test_entries_take_the_ids_after_the_existing_sources(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".research" / "sources" / "s2").mkdir(parents=True)
    artifact = _artifact(tmp_path, ["A", "B"])

    imported = import_literature_from_artifact(str(repo), artifact, "123")

    assert imported == {"s3": "A", "s4": "B"}
    for source_id, entry in (("s3", "0"), ("s4", "1")):
        for name in ("metadata.json", "fulltext.txt"):
            assert (repo / ".research" / "sources" / source_id / name).read_bytes() == (
                artifact / entry / name
            ).read_bytes()
    provenance = SOURCES_PROVENANCE.validate_json(
        (repo / ".research" / "sources" / ".provenance.json").read_bytes()
    )
    assert {k: (v.workflow_run_id, v.entry) for k, v in provenance.items()} == {
        "s3": ("123", "0"),
        "s4": ("123", "1"),
    }


def test_a_second_run_appends_to_the_provenance(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    import_literature_from_artifact(str(repo), _artifact(tmp_path / "a", ["A"]), "1")
    import_literature_from_artifact(str(repo), _artifact(tmp_path / "b", ["B"]), "2")

    provenance = SOURCES_PROVENANCE.validate_json(
        (repo / ".research" / "sources" / ".provenance.json").read_bytes()
    )
    assert {k: v.workflow_run_id for k, v in provenance.items()} == {
        "s1": "1",
        "s2": "2",
    }
