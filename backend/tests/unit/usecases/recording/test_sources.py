"""A source is pinned by its snapshot; a quote is verbatim in it or it is
nothing. Existence is asked of the registry behind each identifier, and a
registry that fails is an error, never a confirmation."""

import subprocess
from pathlib import Path

import httpx
import pytest

from airas.core.research_paths import PAGE_SEPARATOR
from airas.core.types.research_record import LiteratureSource
from airas.research_record.passages import (
    quote_in,
)
from airas.usecases.literature.bibliography import (
    render_references_bib,
    unique_bibkey,
)
from airas.usecases.literature.fulltext_snapshot import (
    snapshot_repository,
    write_fulltext,
)
from airas.usecases.literature.verify_existence import (
    airas_db_metadata,
    verify_existence,
)

PAGES = [
    "Attention Is All You Need\nWe propose the Transformer, a model architecture.",
    "We apply dropout to the output of each sub-layer.\nThe rate is 0.1.",
]


def _fulltext(pages: list[str] = PAGES) -> str:
    return PAGE_SEPARATOR.join(pages)


# ------------------------------------------------------------- the quote


def test_a_quote_copied_from_the_snapshot_is_found() -> None:
    assert quote_in(_fulltext(), "The rate is 0.1.")


def test_whitespace_line_breaks_and_ligatures_do_not_break_a_quote() -> None:
    fulltext = _fulltext(["An eﬃcient\nmethod for  soft­ware."])
    assert quote_in(fulltext, "An efficient method for software.")


def test_a_paraphrase_is_not_found() -> None:
    assert not quote_in(_fulltext(), "Dropout of 0.1 is applied.")


def test_a_quote_spanning_a_page_break_is_found() -> None:
    assert quote_in(_fulltext(), "a model architecture. We apply dropout")


def test_the_snapshot_round_trips_through_the_file(tmp_path: Path) -> None:
    ref = write_fulltext(tmp_path, "s1", PAGES)
    assert ref.path == ".research/sources/s1/fulltext.txt"
    written = (tmp_path / ref.path).read_text(encoding="utf-8")
    assert quote_in(written, "The rate is 0.1.")


def test_a_snapshot_is_not_written_through_a_symlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / ".research" / "sources").mkdir(parents=True)
    (tmp_path / ".research" / "sources" / "s1").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        write_fulltext(tmp_path, "s1", PAGES)
    assert not (outside / "fulltext.txt").exists()


# ----------------------------------------------------------- the bibkey


def test_bibkeys_are_disambiguated_against_registered_sources() -> None:
    title, authors = "Attention Is All You Need", ["Ashish Vaswani"]
    assert unique_bibkey(title, authors, 2017, set()) == "vaswani-2017-attention"
    assert (
        unique_bibkey(title, authors, 2017, {"vaswani-2017-attention"})
        == "vaswani-2017-attentiona"
    )


def test_references_bib_carries_each_source_under_its_bibkey() -> None:
    bib = render_references_bib(
        [
            LiteratureSource(
                id="s1",
                title="Attention Is All You Need",
                authors=["Ashish Vaswani", "Noam Shazeer"],
                year=2017,
                venue="NeurIPS",
                bibkey="vaswani-2017-attention",
            )
        ]
    )
    assert bib.startswith("@article{vaswani-2017-attention,")
    assert "author = {Ashish Vaswani and Noam Shazeer}" in bib
    assert "journal = {NeurIPS}" in bib
    assert bib.endswith("\n")


def test_a_repository_is_a_misc_entry_pinned_to_its_commit() -> None:
    bib = render_references_bib(
        [
            LiteratureSource(
                id="s2",
                kind="repository",
                title="acme/trainer",
                authors=["acme"],
                year=2026,
                url="https://github.com/acme/trainer",
                commit="0123abcd",
                bibkey="acme-2026-trainer",
            )
        ]
    )
    assert bib.startswith("@misc{acme-2026-trainer,")
    assert "note = {commit 0123abcd}" in bib


# ------------------------------------------------------------ a repository


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _upstream(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "trainer"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "uploadpack.allowAnySHA1InWant", "true")
    (repo / "src").mkdir()
    (repo / "src" / "train.py").write_text("lr = 3e-4\nsteps = 1000\n")
    (repo / "README.md").write_text("trainer\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo, _git(repo, "rev-parse", "HEAD")


def test_a_repository_snapshot_holds_the_named_files_at_the_commit(
    tmp_path: Path,
) -> None:
    repo, commit = _upstream(tmp_path)
    metadata, pages = snapshot_repository(str(repo), commit, ["src/train.py"])
    assert metadata["title"].endswith("/trainer")
    assert metadata["commit"] == commit
    assert pages == ["==> src/train.py <==\nlr = 3e-4\nsteps = 1000\n"]
    assert quote_in(PAGE_SEPARATOR.join(pages), "lr = 3e-4")


def test_a_repository_that_cannot_be_fetched_is_refused(tmp_path: Path) -> None:
    repo, _ = _upstream(tmp_path)
    with pytest.raises(ValueError, match="git fetch failed"):
        snapshot_repository(str(repo), "0" * 40, ["src/train.py"])


def test_a_file_missing_at_the_commit_is_refused(tmp_path: Path) -> None:
    repo, commit = _upstream(tmp_path)
    with pytest.raises(ValueError, match="git show failed"):
        snapshot_repository(str(repo), commit, ["src/missing.py"])


# ---------------------------------------------------------- airas-papers-db


def test_a_db_record_yields_what_a_citation_needs() -> None:
    record = {
        "id": "e369",
        "title": "Attention Is All You Need",
        "authors": "['Ashish Vaswani', 'Noam Shazeer']",
        "year": "2017",
        "conference": "neurips",
        "paper_url": "None",
    }
    assert airas_db_metadata(record) == {
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
        "venue": "neurips",
        "url": None,
    }


# ----------------------------------------------------------- the registries

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><entry>
<id>http://arxiv.org/abs/1706.03762v7</id><title>Attention Is All You Need</title>
</entry></feed>"""
EMPTY_ATOM = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'


class _Arxiv:
    def __init__(self, atom: str) -> None:
        self.atom = atom

    async def aget_paper_by_id(self, arxiv_id: str, **_: object) -> str:
        return self.atom


def _doi_org(status: int) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "HEAD" and request.url.host == "doi.org"
        headers = {"location": "https://example.org/paper"} if status == 302 else {}
        return httpx.Response(status, headers=headers)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_each_identifier_is_asked_of_its_own_registry() -> None:
    registries, at = await verify_existence(
        airas_db_record={"id": "e369"},
        doi="10.5555/3295222.3295349",
        arxiv_id="1706.03762",
        arxiv=_Arxiv(ATOM),
        http=_doi_org(302),
    )
    assert registries == {"airas_db": "found", "doi.org": "found", "arxiv": "found"}
    assert at.endswith("+00:00")


async def test_an_unknown_identifier_is_not_found_and_an_outage_is_an_error() -> None:
    def outage(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    registries, _ = await verify_existence(
        airas_db_record={},
        doi="10.1/nope",
        arxiv_id="0000.00000",
        arxiv=_Arxiv(EMPTY_ATOM),
        http=httpx.AsyncClient(transport=httpx.MockTransport(outage)),
    )
    assert registries["airas_db"] == "not_found"
    assert registries["doi.org"].startswith("error: ")
    assert registries["arxiv"] == "not_found"
    assert "found" not in registries.values()


async def test_a_doi_answered_with_a_final_page_is_found_too() -> None:
    registries, _ = await verify_existence(
        airas_db_record=None,
        doi="10.5555/3295222.3295349",
        arxiv_id=None,
        arxiv=_Arxiv(EMPTY_ATOM),
        http=_doi_org(200),
    )
    assert registries == {"doi.org": "found"}


async def test_a_doi_that_does_not_resolve_is_not_found() -> None:
    registries, _ = await verify_existence(
        airas_db_record=None,
        doi="10.1/nope",
        arxiv_id=None,
        arxiv=_Arxiv(EMPTY_ATOM),
        http=_doi_org(404),
    )
    assert registries == {"doi.org": "not_found"}
