"""preregister_record pins the literature the hypothesis rests on in the
freeze commit: a source CI imported into .research/sources/<id>/ is cited by
its id and takes its metadata and text from there, code is snapshotted at
its commit, quotes are checked against the snapshots, and a failure writes
nothing."""

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from airas.core.research_paths import PAGE_SEPARATOR, RECORD_PATH
from airas.core.types.research_record import ResearchRecord
from airas.mcp.tools import record as record_tools
from airas.usecases.literature import resolve_literatures as resolve_module

PAGES = [
    "ATTENTION IS ALL YOU NEED\nWe propose the Transformer.",
    "We apply dropout to the output of each sub-layer.\nThe rate is 0.1.",
]
SEARCH = {"query": "transformer", "sources": ["arxiv"]}
FETCHED_AT = "2026-10-15T00:00:00+00:00"
PAPER_ROW = {
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani"],
    "abstract": None,
    "doi": "10.5555/3295222.3295349",
    "arxiv_id": "1706.03762v7",
    "url": "https://arxiv.org/abs/1706.03762v7",
    "pdf_url": "https://arxiv.org/pdf/1706.03762v7",
    "published_date": "2017-06-12",
    "venue": "neurips",
    "citations": None,
    "source": "arxiv",
    "external_ids": {"arxiv": "1706.03762v7"},
    "search": SEARCH,
    "fetched_at": FETCHED_AT,
    "fulltext": {
        "url": "https://arxiv.org/pdf/1706.03762v7",
        "parser": "pymupdf test",
        "fetched_at": FETCHED_AT,
    },
}
NO_TEXT_ROW = {
    **PAPER_ROW,
    "title": "A Paper Without A PDF",
    "doi": "10.1/no-pdf",
    "arxiv_id": None,
    "pdf_url": None,
    "source": "openalex",
    "fulltext": {"url": None, "error": "the search source gave no pdf_url"},
}
STUDY_ROW = {
    **PAPER_ROW,
    "title": "SAM on CIFAR, revisited",
    "authors": ["auto-res2/sam-cifar (AIRAS)"],
    "doi": None,
    "arxiv_id": None,
    "url": "https://github.com/auto-res2/sam-cifar",
    "pdf_url": None,
    "published_date": "2026-09-10",
    "venue": "airas",
    "source": "airas_records",
    "external_ids": {"airas_record": "auto-res2/sam-cifar@" + "b" * 40},
    "fulltext": None,
    "snapshot": {
        "url": "https://github.com/auto-res2/sam-cifar",
        "commit": "b" * 40,
        "fetched_at": FETCHED_AT,
    },
}
STUDY_PAGE = (
    "==> .research/record.json <==\n"
    '{"statement": "SAM beats SGD on CIFAR-10 accuracy."}\n'
)
REPO = {
    "url": "https://github.com/acme/trainer",
    "commit": "a" * 40,
    "files": ["src/train.py"],
}
REPO_PAGE = "==> src/train.py <==\nlr = 3e-4\nsteps = 1000\n"


def _hypotheses(quoted_passage_ids: list[str] | None = None) -> list[dict[str, Any]]:
    return [
        {
            "id": "h1",
            "statement": "The proposed method beats the baseline.",
            "quoted_passage_ids": quoted_passage_ids or [],
            "claims": [
                {
                    "id": "c1",
                    "statement": "Proposed beats baseline on accuracy.",
                    "rationale": "Head-to-head on the hypothesis's own metric.",
                    "verifier": {"kind": "seyval"},
                    "criterion": {
                        "metric": "accuracy",
                        "subject": "proposed",
                        "reference": "baseline",
                        "op": ">=",
                        "margin": 0.02,
                    },
                    "prediction": {"low": 0.02, "high": 0.04, "basis": "pilot"},
                    "designs": [
                        {
                            "id": "d1",
                            "runs": [{"run_id": "proposed"}, {"run_id": "baseline"}],
                        }
                    ],
                }
            ],
        }
    ]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _import(
    repo: Path, source_id: str, row: dict[str, Any], files: dict[str, str]
) -> None:
    source_dir = repo / ".research" / "sources" / source_id
    source_dir.mkdir(parents=True)
    (source_dir / "metadata.json").write_text(json.dumps(row), encoding="utf-8")
    for name, text in files.items():
        (source_dir / name).write_text(text, encoding="utf-8")


def _repo(tmp_path: Path) -> Path:
    """A clone after fetch_literature.yml imported three sources."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text("{}")
    _import(tmp_path, "s1", PAPER_ROW, {"fulltext.txt": PAGE_SEPARATOR.join(PAGES)})
    _import(tmp_path, "s2", NO_TEXT_ROW, {})
    _import(tmp_path, "s3", STUDY_ROW, {"r1.txt": STUDY_PAGE})
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "template and imported literature")
    return tmp_path


async def _preregister(
    repo: Path, literature: list[dict[str, Any]], quoted_passage_ids=None
):
    return await record_tools.preregister_record(
        str(repo), _hypotheses(quoted_passage_ids), "mdpi", literature=literature
    )


def _snapshot(
    url: str, commit: str, files: list[str], optional_files: Sequence[str] = ()
) -> tuple[dict[str, Any], list[str]]:
    if commit == "0" * 40:
        raise ValueError(f"git fetch failed for {url}@{commit}: not found")
    return (
        {
            "title": "acme/trainer",
            "authors": ["acme"],
            "year": 2026,
            "url": url,
            "commit": commit,
        },
        [REPO_PAGE],
    )


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resolve_module, "fetch_fulltext_from_repository", _snapshot)


def _untouched(repo: Path) -> None:
    assert (repo / RECORD_PATH).read_text() == "{}"
    assert _git(repo, "status", "--porcelain") == ""


async def test_an_imported_paper_is_pinned_with_the_metadata_ci_fetched(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)

    result = await _preregister(repo, [{"source_id": "s1"}])

    assert result["sources"]["s1"]["bibkey"] == "vaswani-2017-attention"
    source = ResearchRecord.load(str(repo)).literature[0]
    assert (
        source.id,
        source.title,
        source.authors,
        source.year,
        source.venue,
        source.doi,
        source.arxiv_id,
        source.verified_by,
        source.verified_at,
        source.parser,
    ) == (
        "s1",
        "Attention Is All You Need",
        ["Ashish Vaswani"],
        2017,
        "neurips",
        "10.5555/3295222.3295349",
        "1706.03762v7",
        "arxiv",
        FETCHED_AT,
        "pymupdf test",
    )
    assert source.fulltext is not None
    assert source.fulltext.path == ".research/sources/s1/fulltext.txt"
    assert (
        "vaswani-2017-attention"
        in (repo / ".research" / "latex" / "mdpi" / "references.bib").read_text()
    )
    # record, claims.tex and references.bib in one commit; the imported text untouched
    assert _git(repo, "rev-list", "--count", "HEAD") == "2"
    assert _git(repo, "status", "--porcelain") == ""
    assert _git(repo, "diff", "HEAD~1", "--name-only", "--", ".research/sources") == ""


async def test_a_source_ci_did_not_import_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="was not imported"):
        await _preregister(repo, [{"source_id": "s9"}])
    _untouched(repo)


async def test_a_source_whose_text_could_not_be_fetched_cannot_be_cited(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="no text was fetched"):
        await _preregister(repo, [{"source_id": "s2"}])
    _untouched(repo)


async def test_an_entry_that_names_neither_a_source_nor_code_is_refused(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="cite an imported source by source_id"):
        await _preregister(repo, [{"doi": "10.5555/3295222.3295349"}])
    _untouched(repo)


async def test_passages_get_ids_and_ground_the_hypothesis(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            "source_id": "s1",
            "passages": [{"node_type": "setup", "quote": "The rate is 0.1."}],
        }
    ]

    result = await _preregister(repo, literature, quoted_passage_ids=["s1.p1"])

    assert result["sources"]["s1"]["passages"] == ["s1.p1"]
    record = ResearchRecord.load(str(repo))
    assert record.hypotheses[0].quoted_passage_ids == ["s1.p1"]
    claims_tex = (repo / ".research" / "latex" / "mdpi" / "claims.tex").read_text()
    assert r"\cite[s1.p1]{vaswani-2017-attention}" in claims_tex


async def test_a_quote_not_in_the_snapshot_is_refused_and_nothing_is_written(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            "source_id": "s1",
            "passages": [{"node_type": "setup", "quote": "Dropout is 0.1."}],
        }
    ]
    with pytest.raises(ValueError, match="not found verbatim"):
        await _preregister(repo, literature)
    _untouched(repo)


async def test_a_passage_no_source_declares_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="no source declares"):
        await _preregister(repo, [], quoted_passage_ids=["s1.p1"])
    _untouched(repo)


async def test_a_passage_id_cannot_be_passed_in(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            "source_id": "s1",
            "passages": [
                {"id": "s2.p1", "node_type": "setup", "quote": "The rate is 0.1."}
            ],
        }
    ]
    with pytest.raises(ValueError, match="assigned by its source"):
        await _preregister(repo, literature)
    _untouched(repo)


async def test_the_same_source_twice_is_pinned_once(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    await _preregister(repo, [{"source_id": "s1"}, {"source_id": "s1"}])
    assert [s.id for s in ResearchRecord.load(str(repo)).literature] == ["s1"]


# ------------------------------------------------------------ repositories


async def test_code_with_no_paper_takes_the_next_id_after_the_imported_sources(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            "repositories": [{**REPO, "method_entry": "train.main"}],
            "passages": [{"node_type": "setup", "quote": "lr = 3e-4"}],
        }
    ]

    result = await _preregister(repo, literature)

    source = ResearchRecord.load(str(repo)).literature[0]
    assert (source.id, source.repositories[0].commit, source.verified_by) == (
        "s4",
        "a" * 40,
        "git",
    )
    assert source.repositories[0].method_entry == "train.main"
    assert source.fulltext is None  # no paper: the work is the code
    assert result["sources"]["s4"]["passages"] == ["s4.p1"]
    assert (repo / source.repositories[0].snapshot.path).read_text() == REPO_PAGE


async def test_an_imported_paper_and_the_code_it_ships_are_one_source(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            "source_id": "s1",
            "repositories": [REPO],
            "passages": [
                {"node_type": "method", "quote": "We apply dropout"},
                {"node_type": "setup", "quote": "lr = 3e-4"},
            ],
        }
    ]

    await _preregister(repo, literature)

    record = ResearchRecord.load(str(repo))
    assert [s.id for s in record.literature] == ["s1"]
    source = record.literature[0]
    assert (source.verified_by, source.repositories[0].id) == ("arxiv", "s1.r1")
    assert (repo / source.fulltext.path).read_text() == PAGE_SEPARATOR.join(PAGES)
    assert (repo / source.repositories[0].snapshot.path).read_text() == REPO_PAGE


async def test_code_appended_to_a_pinned_paper_joins_it_as_the_next_repository(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    await _preregister(repo, [{"source_id": "s1"}])

    await record_tools.append_to_record(
        str(repo), literature=[{"source_id": "s1", "repositories": [REPO]}]
    )

    record = ResearchRecord.load(str(repo))
    assert [s.id for s in record.literature] == ["s1"]
    assert [r.id for r in record.literature[0].repositories] == ["s1.r1"]
    assert (
        repo / record.literature[0].repositories[0].snapshot.path
    ).read_text() == REPO_PAGE


async def test_a_repository_that_cannot_be_fetched_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="git fetch failed"):
        await _preregister(repo, [{"repositories": [{**REPO, "commit": "0" * 40}]}])
    _untouched(repo)


async def test_a_repository_needs_url_commit_and_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="url, commit and files"):
        await _preregister(
            _repo(tmp_path),
            [{"repositories": [{"url": REPO["url"], "commit": REPO["commit"]}]}],
        )


async def test_a_repository_commit_must_be_a_full_sha(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="full 40-hex sha"):
        await _preregister(
            _repo(tmp_path), [{"repositories": [{**REPO, "commit": "main"}]}]
        )


# ------------------------------------------------- a study AIRAS produced


async def test_an_imported_airas_study_is_pinned_by_its_record_at_the_commit(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            "source_id": "s3",
            "passages": [
                {"node_type": "result", "quote": "SAM beats SGD on CIFAR-10 accuracy."}
            ],
        }
    ]

    result = await _preregister(repo, literature)

    source = ResearchRecord.load(str(repo)).literature[0]
    assert (source.verified_by, source.parser, source.fulltext) == (
        "airas_records",
        "git show",
        None,
    )
    assert (source.repositories[0].id, source.repositories[0].commit) == (
        "s3.r1",
        "b" * 40,
    )
    assert source.repositories[0].snapshot.path == ".research/sources/s3/r1.txt"
    assert result["sources"]["s3"]["passages"] == ["s3.p1"]
    assert (
        "@misc{"
        in (repo / ".research" / "latex" / "mdpi" / "references.bib").read_text()
    )


# --------------------------------------------------------- after the freeze


async def test_literature_appended_after_the_freeze_is_committed_with_the_bib(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    await _preregister(repo, [{"source_id": "s1"}])

    result = await record_tools.append_to_record(
        str(repo), literature=[{"repositories": [REPO]}]
    )

    assert list(result["appended"]["literature"]) == ["s4"]
    assert [s.id for s in ResearchRecord.load(str(repo)).literature] == ["s1", "s4"]
    assert (
        "acme-2026-trainer"
        in (repo / ".research" / "latex" / "mdpi" / "references.bib").read_text()
    )
    assert _git(repo, "rev-list", "--count", "HEAD") == "3"
    assert _git(repo, "status", "--porcelain") == ""


async def test_passages_append_under_their_source_and_must_be_verbatim(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    await _preregister(repo, [{"source_id": "s1"}])

    result = await record_tools.append_to_record(
        str(repo),
        source_id="s1",
        passages=[{"node_type": "setup", "quote": "The rate is 0.1."}],
    )
    assert result["appended"]["passages"] == 1
    assert [p.id for p in ResearchRecord.load(str(repo)).literature[0].passages] == [
        "s1.p1"
    ]

    with pytest.raises(ValueError, match="not found verbatim"):
        await record_tools.append_to_record(
            str(repo),
            source_id="s1",
            passages=[{"node_type": "setup", "quote": "Dropout is 0.1."}],
        )
    assert [p.id for p in ResearchRecord.load(str(repo)).literature[0].passages] == [
        "s1.p1"
    ]


async def test_passages_without_a_source_are_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pass source_id"):
        await record_tools.append_to_record(
            str(_repo(tmp_path)), passages=[{"node_type": "claim", "quote": "q"}]
        )


async def test_a_failed_commit_leaves_the_clone_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """record.json, claims.tex, references.bib and any snapshot are written
    before the commit; a commit that fails must take them all back, or the
    record would point at files that are gone."""
    from airas.research_record.update import preregister_record as prereg

    repo = _repo(tmp_path)

    def _boom(*_a: Any, **_k: Any) -> str:
        raise RuntimeError("git commit failed: no identity")

    monkeypatch.setattr(prereg, "commit_paths", _boom)
    with pytest.raises(RuntimeError, match="git commit failed"):
        await _preregister(repo, [{"source_id": "s1", "repositories": [REPO]}])
    _untouched(repo)
    assert not (repo / ".research" / "latex").exists()
