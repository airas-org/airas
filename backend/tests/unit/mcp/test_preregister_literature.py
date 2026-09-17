"""preregister_record pins the literature the hypothesis rests on in the
freeze commit: a registry must confirm each source, the full text is
snapshotted, quotes are checked against it, and a failure writes nothing."""

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from airas.core.research_paths import PAGE_SEPARATOR, RECORD_PATH
from airas.core.types.research_record import ResearchRecord
from airas.infra.airas_records_index import RecordEntry
from airas.mcp.tools import record as record_tools
from airas.research_record.read.load_record import load_record
from airas.research_record.update import _resolve_literatures as verify_module

PAGES = [
    "ATTENTION IS ALL YOU NEED\nWe propose the Transformer.",
    "We apply dropout to the output of each sub-layer.\nThe rate is 0.1.",
]
DB_RECORD = {
    "id": "e369",
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani"],
    "year": "2017",
    "conference": "neurips",
    "paper_url": "https://example.org/attention.pdf",
}
DB_PAPER = {"airas_db": "e369"}
REPO = {
    "url": "https://github.com/acme/trainer",
    "commit": "a" * 40,
    "files": ["src/train.py"],
}
REPO_PAGE = "==> src/train.py <==\nlr = 3e-4\nsteps = 1000\n"
STUDY = "auto-res2/sam-cifar@" + "b" * 40
CLAIMS_PAGE = (
    "==> .research/latex/mdpi/claims.tex <==\n"
    "\\item[\\textbf{C1}] SAM beats SGD on CIFAR-10 accuracy.\n"
    "  \\emph{Verdict:} refuted.\n"
)


def _hypotheses(grounded_on: list[str] | None = None) -> list[dict[str, Any]]:
    return [
        {
            "id": "h1",
            "statement": "The proposed method beats the baseline.",
            "grounded_on": grounded_on or [],
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


def _repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")
    (tmp_path / RECORD_PATH).parent.mkdir(parents=True)
    (tmp_path / RECORD_PATH).write_text("{}")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "template")
    return tmp_path


async def _preregister(repo: Path, literature: list[dict[str, Any]], grounded_on=None):
    return await record_tools.preregister_record(
        str(repo), _hypotheses(grounded_on), "mdpi", literature=literature
    )


class _Index:
    async def get(self, record_id: str) -> dict[str, Any] | None:
        return DB_RECORD if record_id == "e369" else None


class _Records:
    async def get(self, record_id: str) -> RecordEntry | None:
        if record_id != STUDY:
            return None
        return RecordEntry(
            id=STUDY,
            url="https://github.com/auto-res2/sam-cifar",
            commit="b" * 40,
            stage="results",
            collected_at="2026-09-10T00:00:00+00:00",
            title="SAM on CIFAR, revisited",
            record=ResearchRecord(),
        )


class _Fetch:
    calls: list[dict[str, Any]] = []

    @staticmethod
    async def pages(arxiv_id, doi, pdf_url, _client) -> dict[str, Any]:
        _Fetch.calls.append({"arxiv_id": arxiv_id, "doi": doi, "pdf_url": pdf_url})
        return {"status": "fulltext", "pages": PAGES, "pdf_url": pdf_url}


async def _verify(**kw: Any) -> tuple[dict[str, str], str]:
    registries = {}
    if kw["airas_db_record"] is not None:
        registries["airas_db"] = "found" if kw["airas_db_record"] else "not_found"
    if kw["doi"]:
        registries["doi.org"] = "found" if kw["doi"] != "10.1/nope" else "not_found"
    return registries, "2026-09-15T00:00:00+00:00"


def _snapshot(
    url: str, commit: str, files: list[str], optional_files: Sequence[str] = ()
) -> tuple[dict[str, Any], list[str]]:
    if commit == "0" * 40:
        raise ValueError(f"git fetch failed for {url}@{commit}: not found")
    pages = (
        [REPO_PAGE]
        if "src/train.py" in files
        else ["==> .research/record.json <==\n{}\n"]
    )
    if any(p.endswith("mdpi/claims.tex") for p in optional_files):
        pages.append(CLAIMS_PAGE)
    return (
        {
            "title": "acme/trainer",
            "authors": ["acme"],
            "year": 2026,
            "url": url,
            "commit": commit,
        },
        pages,
    )


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(record_tools, "_search_index", _Index())
    monkeypatch.setattr(record_tools, "_records_index", _Records())
    monkeypatch.setattr(record_tools, "_semantic_scholar_client", lambda: object())
    monkeypatch.setattr(record_tools, "_arxiv_client", lambda: object())
    monkeypatch.setattr(verify_module, "_verify_paper_existence", _verify)
    monkeypatch.setattr(verify_module, "fetch_fulltext_from_repository", _snapshot)
    monkeypatch.setattr(verify_module, "_fulltext_pages", _Fetch.pages)
    monkeypatch.setattr(verify_module, "parser_version", lambda: "pymupdf test")
    _Fetch.calls = []


def _untouched(repo: Path) -> None:
    assert not (repo / ".research" / "sources").exists()
    assert (repo / RECORD_PATH).read_text() == "{}"
    assert _git(repo, "status", "--porcelain") == ""


async def test_a_db_paper_is_pinned_in_the_freeze_commit(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    result = await _preregister(repo, [DB_PAPER])

    assert result["sources"]["s1"]["bibkey"] == "vaswani-2017-attention"
    assert result["sources"]["s1"]["verified_by"] == "airas_db"
    assert _Fetch.calls[0]["pdf_url"] == DB_RECORD["paper_url"]
    snapshot = repo / ".research" / "sources" / "s1" / "fulltext.txt"
    assert snapshot.read_text(encoding="utf-8") == PAGE_SEPARATOR.join(PAGES)
    record = load_record(str(repo))
    source = record.literature[0]
    assert (source.url, source.venue, source.year) == (
        DB_RECORD["paper_url"],
        "neurips",
        2017,
    )
    assert record.hypotheses[0].id == "h1"
    assert (
        "vaswani-2017-attention"
        in (repo / ".research" / "latex" / "mdpi" / "references.bib").read_text()
    )
    # literature, record, claims.tex and references.bib: one commit, nothing left over
    assert _git(repo, "rev-list", "--count", "HEAD") == "2"
    assert _git(repo, "status", "--porcelain") == ""


async def test_the_text_fetch_paper_fulltext_wrote_is_used_instead_of_a_download(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    cached = tmp_path / "cache.txt"
    cached.write_text(PAGE_SEPARATOR.join(PAGES), encoding="utf-8")

    await _preregister(repo, [{**DB_PAPER, "fulltext_path": str(cached)}])

    assert _Fetch.calls == []
    snapshot = repo / ".research" / "sources" / "s1" / "fulltext.txt"
    assert snapshot.read_text(encoding="utf-8") == cached.read_text(encoding="utf-8")


async def test_a_paper_the_agent_found_on_the_web_gets_the_same_check(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    paper = {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani"],
        "year": 2017,
        "venue": "NeurIPS",
        "doi": "10.5555/3295222.3295349",
        "pdf_url": "https://example.org/found-by-search.pdf",
    }
    result = await _preregister(repo, [paper])
    assert result["sources"]["s1"]["verified_by"] == "doi.org"
    assert load_record(str(repo)).literature[0].doi == paper["doi"]


async def test_a_paper_with_no_identifier_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="existence can be checked"):
        await _preregister(repo, [{"title": "t", "pdf_url": "https://x/y.pdf"}])
    _untouched(repo)


async def test_a_paper_no_registry_confirms_is_refused_and_nothing_is_written(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="no registry verified it"):
        await _preregister(repo, [{"doi": "10.1/nope", "title": "t"}])
    assert _Fetch.calls == []
    _untouched(repo)


async def test_a_failure_on_a_later_paper_leaves_no_snapshot_behind(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="no registry verified it"):
        await _preregister(repo, [DB_PAPER, {"doi": "10.1/nope", "title": "t"}])
    _untouched(repo)


async def test_a_pdf_that_does_not_carry_the_title_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    paper = {
        "title": "Some Other Paper",
        "doi": "10.5555/1",
        "pdf_url": "https://x/y.pdf",
    }
    with pytest.raises(ValueError, match="do not carry this title"):
        await _preregister(repo, [paper])
    _untouched(repo)


async def test_passages_get_ids_and_ground_the_hypothesis(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    literature = [
        {**DB_PAPER, "passages": [{"node_type": "setup", "quote": "The rate is 0.1."}]}
    ]

    result = await _preregister(repo, literature, grounded_on=["s1.p1"])

    assert result["sources"]["s1"]["passages"] == ["s1.p1"]
    record = load_record(str(repo))
    assert record.hypotheses[0].grounded_on == ["s1.p1"]
    claims_tex = (repo / ".research" / "latex" / "mdpi" / "claims.tex").read_text()
    assert "Grounded on" in claims_tex and "The rate is 0.1." in claims_tex


async def test_a_quote_not_in_the_snapshot_is_refused_and_nothing_is_written(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    literature = [
        {**DB_PAPER, "passages": [{"node_type": "setup", "quote": "Dropout is 0.1."}]}
    ]
    with pytest.raises(ValueError, match="not found verbatim"):
        await _preregister(repo, literature)
    _untouched(repo)


async def test_a_passage_no_source_declares_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="no source declares"):
        await _preregister(repo, [], grounded_on=["s1.p1"])
    _untouched(repo)


async def test_a_passage_id_cannot_be_passed_in(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            **DB_PAPER,
            "passages": [
                {"id": "s2.p1", "node_type": "setup", "quote": "The rate is 0.1."}
            ],
        }
    ]
    with pytest.raises(ValueError, match="assigned by its source"):
        await _preregister(repo, literature)
    _untouched(repo)


async def test_the_same_paper_twice_is_pinned_once(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    await _preregister(repo, [DB_PAPER, DB_PAPER])
    assert [s.id for s in load_record(str(repo)).literature] == ["s1"]


# ------------------------------------------------------------ repositories


async def test_a_repository_is_pinned_at_its_commit_with_its_files(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            **REPO,
            "passages": [
                {"node_type": "setup", "anchor": "code", "quote": "lr = 3e-4"}
            ],
        }
    ]

    result = await _preregister(repo, literature)

    source = load_record(str(repo)).literature[0]
    assert (source.kind, source.commit, source.bibkey) == (
        "repository",
        "a" * 40,
        "acme-2026-trainer",
    )
    assert source.verified_by == "git"
    assert [p.anchor for p in source.passages] == ["code"]
    assert result["sources"]["s1"]["passages"] == ["s1.p1"]
    assert (repo / source.fulltext.path).read_text() == REPO_PAGE


async def test_a_repository_that_cannot_be_fetched_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="git fetch failed"):
        await _preregister(repo, [{**REPO, "commit": "0" * 40}])
    _untouched(repo)


async def test_a_repository_needs_url_commit_and_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="url, commit and files"):
        await _preregister(
            _repo(tmp_path), [{"url": REPO["url"], "commit": REPO["commit"]}]
        )


async def test_a_repository_commit_must_be_a_full_sha(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="full 40-hex sha"):
        await _preregister(_repo(tmp_path), [{**REPO, "commit": "main"}])


# ------------------------------------------------- a study AIRAS produced


async def test_an_airas_record_is_pinned_by_its_record_and_claims(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    literature = [
        {
            "airas_record": STUDY,
            "passages": [
                {"node_type": "result", "quote": "SAM beats SGD on CIFAR-10 accuracy."}
            ],
        }
    ]

    result = await _preregister(repo, literature)

    source = load_record(str(repo)).literature[0]
    assert (source.kind, source.verified_by, source.commit) == (
        "airas_record",
        "airas_records",
        "b" * 40,
    )
    assert (source.title, source.authors, source.bibkey) == (
        "SAM on CIFAR, revisited",
        ["auto-res2/sam-cifar (AIRAS)"],
        "samcifar-2026-sam",
    )
    assert result["sources"]["s1"]["passages"] == ["s1.p1"]
    assert CLAIMS_PAGE in (repo / source.fulltext.path).read_text()
    assert (
        "@misc{samcifar-2026-sam,"
        in (repo / ".research" / "latex" / "mdpi" / "references.bib").read_text()
    )


async def test_a_study_not_in_the_store_is_refused(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="not in airas-records-db"):
        await _preregister(repo, [{"airas_record": "auto-res2/other@" + "c" * 40}])
    _untouched(repo)


# --------------------------------------------------------- after the freeze


async def test_literature_appended_after_the_freeze_is_committed_with_the_bib(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    await _preregister(repo, [DB_PAPER])

    result = await record_tools.append_to_record(str(repo), literature=[REPO])

    assert list(result["appended"]["literature"]) == ["s2"]
    assert [s.id for s in load_record(str(repo)).literature] == ["s1", "s2"]
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
    await _preregister(repo, [DB_PAPER])

    result = await record_tools.append_to_record(
        str(repo),
        source_id="s1",
        passages=[{"node_type": "setup", "quote": "The rate is 0.1."}],
    )
    assert result["appended"]["passages"] == 1
    assert [p.id for p in load_record(str(repo)).literature[0].passages] == ["s1.p1"]

    with pytest.raises(ValueError, match="not found verbatim"):
        await record_tools.append_to_record(
            str(repo),
            source_id="s1",
            passages=[{"node_type": "setup", "quote": "Dropout is 0.1."}],
        )
    assert [p.id for p in load_record(str(repo)).literature[0].passages] == ["s1.p1"]


async def test_passages_without_a_source_are_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pass source_id"):
        await record_tools.append_to_record(
            str(_repo(tmp_path)), passages=[{"node_type": "claim", "quote": "q"}]
        )
