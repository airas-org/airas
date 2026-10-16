"""A keyword query matches papers that carry every keyword, not any one of them."""

import httpx

from airas.infra.arxiv_client import ArxivClient


def _query(query: str, **kw: str) -> str:
    return ArxivClient._build_search_query(
        object.__new__(ArxivClient),
        query,
        title=None,
        author=None,
        from_date=kw.get("from_date"),
        to_date=kw.get("to_date"),
        search_field="all",
    )


def test_each_keyword_is_searched_in_the_field_and_all_are_required() -> None:
    assert _query("sharpness  aware minimization") == (
        "all:sharpness AND all:aware AND all:minimization"
    )


def test_a_colon_cannot_name_another_field() -> None:
    assert _query("ti:attention") == "all:tiattention"


def test_the_date_range_applies_to_the_whole_query() -> None:
    assert _query("sam cifar", from_date="20200101", to_date="20201231") == (
        "(all:sam AND all:cifar) AND submittedDate:[20200101 TO 20201231]"
    )


def test_a_quoted_phrase_stays_one_term() -> None:
    assert _query('"sharpness aware minimization"') == (
        'all:"sharpness aware minimization"'
    )


def test_a_phrase_and_keywords_are_all_required() -> None:
    assert _query('"machine learning" optimization') == (
        'all:"machine learning" AND all:optimization'
    )


def test_an_unclosed_quote_is_dropped() -> None:
    assert _query('"machine learning') == "all:machine AND all:learning"


async def test_id_lookup_sends_the_requested_version() -> None:
    requested = []

    def respond(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.params["id_list"])
        return httpx.Response(200, text="<feed/>")

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as session:
        client = ArxivClient(async_session=session)
        await client.aget_paper_by_id(" 1706.03762v1 ")
    assert requested == ["1706.03762v1"]
