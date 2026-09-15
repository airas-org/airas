"""register_sources pins a paper its registry confirms and refuses one it
does not, writing nothing; passages append under their source and are
checked against the snapshot before anything is committed."""

import subprocess
from pathlib import Path
from typing import Any

import pytest

from airas.core.research_paths import RECORD_PATH
from airas.mcp import server
from airas.usecases.recording.update_or_load_record import load_record

PAGES = [
    "Attention Is All You Need\nWe propose the Transformer.",
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


def _hypotheses(grounded_on: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "id": "h1",
            "statement": "The proposed method beats the baseline.",
            "grounded_on": grounded_on,
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


class _Index:
    async def get(self, record_id: str) -> dict[str, Any] | None:
        return DB_RECORD if record_id == "e369" else None


class _Fetch:
    calls: list[dict[str, Any]] = []

    def __init__(self, **_: object) -> None:
        pass

    def build_graph(self):
        return self

    async def ainvoke(self, inputs: dict[str, Any]) -> dict[str, Any]:
        _Fetch.calls.append(inputs)
        return {"status": "fulltext", "pages": PAGES, "pdf_url": inputs["pdf_url"]}


async def _verify(**kw: Any) -> tuple[dict[str, str], str]:
    registries = {}
    if kw["airas_db_record"] is not None:
        registries["airas_db"] = "found" if kw["airas_db_record"] else "not_found"
    if kw["doi"]:
        registries["doi.org"] = "found" if kw["doi"] != "10.1/nope" else "not_found"
    return registries, "2026-09-15T00:00:00+00:00"


REPO_PAGE = "==> src/train.py <==\nlr = 3e-4\nsteps = 1000\n"


def _snapshot(
    url: str, commit: str, files: list[str]
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
    monkeypatch.setattr(server, "_search_index", _Index())
    monkeypatch.setattr(server, "verify_existence", _verify)
    monkeypatch.setattr(server, "snapshot_repository", _snapshot)
    monkeypatch.setattr(server, "FetchPaperFulltextSubgraph", _Fetch)
    monkeypatch.setattr(server, "_semantic_scholar_client", lambda: object())
    monkeypatch.setattr(server, "_arxiv_client", lambda: object())
    monkeypatch.setattr(server, "parser_version", lambda: "pymupdf test")
    _Fetch.calls = []


async def test_a_db_paper_is_pinned_from_its_record_and_committed(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)

    result = await server.register_sources(str(repo), [{"airas_db": "e369"}])

    assert result["sources"]["s1"]["bibkey"] == "vaswani-2017-attention"
    assert result["sources"]["s1"]["verified_by"] == "airas_db"
    assert _Fetch.calls[0]["pdf_url"] == DB_RECORD["paper_url"]
    snapshot = repo / ".research" / "sources" / "s1" / "fulltext.txt"
    assert snapshot.read_text(encoding="utf-8") == "\f".join(PAGES)
    source = load_record(str(repo)).literature[0]
    assert (source.url, source.venue, source.year) == (
        DB_RECORD["paper_url"],
        "neurips",
        2017,
    )
    assert _git(repo, "rev-list", "--count", "HEAD") == "2"
    assert _git(repo, "status", "--porcelain") == ""


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

    result = await server.register_sources(str(repo), [paper])

    assert result["sources"]["s1"]["verified_by"] == "doi.org"
    assert load_record(str(repo)).literature[0].doi == paper["doi"]


async def test_a_paper_with_no_identifier_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="existence can be checked"):
        await server.register_sources(
            str(_repo(tmp_path)), [{"title": "t", "pdf_url": "https://x/y.pdf"}]
        )


async def test_a_paper_no_registry_confirms_is_refused_and_nothing_is_written(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)

    with pytest.raises(ValueError, match="no registry verified it"):
        await server.register_sources(str(repo), [{"doi": "10.1/nope", "title": "t"}])

    assert _Fetch.calls == []
    assert not (repo / ".research" / "sources").exists()
    assert _git(repo, "status", "--porcelain") == ""


async def test_registering_the_same_paper_again_leaves_it_as_it_is(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    await server.register_sources(str(repo), [{"airas_db": "e369"}])
    before = load_record(str(repo)).literature

    await server.register_sources(str(repo), [{"airas_db": "e369"}])

    assert load_record(str(repo)).literature == before
    assert len(_Fetch.calls) == 1


async def test_passages_append_under_their_source_and_must_be_verbatim(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    await server.register_sources(str(repo), [{"airas_db": "e369"}])

    result = await server.append_to_record(
        str(repo),
        source_id="s1",
        passages=[{"node_type": "setup", "quote": "The rate is 0.1."}],
    )
    assert result["appended"]["passages"] == 1
    assert [p.id for p in load_record(str(repo)).literature[0].passages] == ["s1.p1"]

    with pytest.raises(ValueError, match="not found verbatim"):
        await server.append_to_record(
            str(repo),
            source_id="s1",
            passages=[{"node_type": "setup", "quote": "Dropout is 0.1."}],
        )
    assert [p.id for p in load_record(str(repo)).literature[0].passages] == ["s1.p1"]


async def test_passages_without_a_source_are_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pass source_id"):
        await server.append_to_record(
            str(_repo(tmp_path)), passages=[{"node_type": "claim", "quote": "q"}]
        )


async def test_preregister_keeps_the_sources_registered_before_it(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    await server.register_sources(
        str(repo),
        [
            {
                "airas_db": "e369",
                "passages": [{"node_type": "setup", "quote": "The rate is 0.1."}],
            }
        ],
    )

    await server.preregister_record(str(repo), _hypotheses(["s1.p1"]), "mdpi")

    record = load_record(str(repo))
    assert [s.id for s in record.literature] == ["s1"]
    assert record.hypotheses[0].grounded_on == ["s1.p1"]
    claims_tex = (repo / ".research" / "latex" / "mdpi" / "claims.tex").read_text()
    assert "Grounded on" in claims_tex and "The rate is 0.1." in claims_tex


async def test_a_passage_no_source_declares_is_refused_at_preregistration(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="no source declares"):
        await server.preregister_record(
            str(_repo(tmp_path)), _hypotheses(["s1.p1"]), "mdpi"
        )


# ------------------------------------------------------------ repositories

REPO = {
    "url": "https://github.com/acme/trainer",
    "commit": "a" * 40,
    "files": ["src/train.py"],
}


async def test_a_repository_is_pinned_at_its_commit_with_its_files(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)

    result = await server.register_sources(
        str(repo),
        repositories=[
            {
                **REPO,
                "passages": [
                    {"node_type": "setup", "anchor": "code", "quote": "lr = 3e-4"}
                ],
            }
        ],
    )

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
        await server.register_sources(
            str(repo), repositories=[{**REPO, "commit": "0" * 40}]
        )
    assert _git(repo, "status", "--porcelain") == ""


async def test_a_repository_needs_url_commit_and_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="url, commit and files"):
        await server.register_sources(
            str(_repo(tmp_path)), repositories=[{"url": REPO["url"]}]
        )


async def test_the_same_repository_and_commit_is_registered_once(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    await server.register_sources(str(repo), repositories=[REPO])
    await server.register_sources(str(repo), repositories=[REPO])
    assert [s.id for s in load_record(str(repo)).literature] == ["s1"]


async def test_nothing_to_register_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="nothing to register"):
        await server.register_sources(str(_repo(tmp_path)))


async def test_a_passage_id_cannot_be_passed_in(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    await server.register_sources(str(repo), [{"airas_db": "e369"}])
    with pytest.raises(ValueError, match="assigned by its source"):
        await server.append_to_record(
            str(repo),
            source_id="s1",
            passages=[
                {"id": "s2.p1", "node_type": "setup", "quote": "The rate is 0.1."}
            ],
        )


async def test_a_failure_on_a_later_paper_leaves_no_snapshot_behind(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="no registry verified it"):
        await server.register_sources(
            str(repo), [{"airas_db": "e369"}, {"doi": "10.1/nope", "title": "t"}]
        )
    assert not (repo / ".research" / "sources").exists()
    assert _git(repo, "status", "--porcelain") == ""
