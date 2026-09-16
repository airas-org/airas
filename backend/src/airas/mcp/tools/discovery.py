"""Paper discovery and hypothesis generation."""

import os
from typing import Any, Literal

from airas.core.credentials import SETUP_INSTRUCTIONS, refresh_environment
from airas.core.llm_config import uniform_llm_mapping
from airas.core.types.research_study import ResearchStudy
from airas.mcp.app import mcp
from airas.mcp.context import (
    _arxiv_client,
    _github_client,
    _litellm_client,
    _openalex_client,
    _records_index,
    _search_index,
    _semantic_scholar_client,
)
from airas.mcp.prompt_registry import build_generation_prompt, get_input_json_schema
from airas.usecases.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0,
    GenerateHypothesisSubgraphV0LLMMapping,
)
from airas.usecases.generators.generate_queries_subgraph.generate_queries_subgraph import (
    GenerateQueriesLLMMapping,
    GenerateQueriesSubgraph,
)
from airas.usecases.literature import search_papers as search_papers_usecase
from airas.usecases.retrieve.fetch_paper_fulltext_subgraph.fetch_paper_fulltext_subgraph import (
    FetchPaperFulltextSubgraph,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
    RetrievePaperSubgraphLLMMapping,
)


@mcp.tool()
def get_generation_prompt(step: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Assemble AIRAS's curated prompt(s) for a generation step so you (the
    MCP host) can author the artifact yourself — no LLM API key required.

    Generation steps run in one of two modes: the backend-LLM tool
    (`generate_research_queries` / `analyze_experiment` / `generate_paper`,
    needs a provider key) or host mode via this tool. Both use the same
    prompt templates, so quality guidance is identical. Prefer host mode
    when no LLM provider key is configured, or when your own context (the
    conversation, code you wrote) should inform the writing.

    `step` and the required `inputs` keys:
    - "research_queries": research_topic, num_queries (optional)
    - "hypothesis": research_topic, research_study_list
    - "experimental_design": research_hypothesis, compute_environment
      (optional), num_models_to_use / num_datasets_to_use /
      num_comparative_methods (optional)
    - "experiment_analysis": research_hypothesis, experimental_design,
      experiment_code ({"files": {path: content}}), experimental_results
    - "paper_writing": research_hypothesis, experiment_history,
      experiment_code, research_study_list, references_bib
    - "latex_conversion": paper_content, figures_dir (optional)

    Returns a fully rendered `prompt`, an `input_json_schema` describing the
    exact shape of `inputs` for this step, an `output_json_schema` describing
    exactly the data format to produce in one pass, and a `flow` note on
    how the output feeds the next step. Call `get_input_schema` first if you
    are assembling an input by hand — `research_study_list` entries in
    particular are `ResearchStudy` objects, not `search_papers` rows, and
    share no key names with them.
    """
    return build_generation_prompt(step, inputs)


@mcp.tool()
def get_input_schema(step: str) -> dict[str, Any]:
    """The JSON Schema of an input a tool takes.

    Use before assembling one by hand, so the shape is known up front
    instead of being discovered through a validation error — or, worse, not
    discovered at all. `step` is any of `get_generation_prompt`'s steps, or
    `research_history` for what `upload_research_history` accepts. No API
    keys required.

    Assembling `research_study_list` from `search_papers` output is the
    common case and needs a translation: a search row's `authors`,
    `citations` and `arxiv_id` live under `meta_data` on a `ResearchStudy`,
    and only `title` is required — a study with just `title` and `abstract`
    is valid, so nothing has to be invented for papers whose full text was
    not retrieved.
    """
    return get_input_json_schema(step)


@mcp.tool()
async def generate_research_queries(
    research_topic: str,
    model: str,
    num_queries: int = 2,
) -> list[str]:
    """Generate academic paper search queries from a research topic (backend LLM).

    Use this first to turn a free-form research topic into effective
    search queries, then pass them to `search_papers`. `model` is required
    (the LLM to use) — call `get_available_llms` to see which models the
    configured keys allow. Requires an LLM provider API key — without one,
    use `get_generation_prompt(step="research_queries", ...)` and author the
    queries yourself.
    """
    result = (
        await GenerateQueriesSubgraph(
            llm_client=_litellm_client(),
            num_paper_search_queries=num_queries,
            llm_mapping=uniform_llm_mapping(GenerateQueriesLLMMapping, model),
        )
        .build_graph()
        .ainvoke({"research_topic": research_topic})
    )
    return result["queries"]


@mcp.tool()
async def search_papers(
    query: str,
    sources: str = "all",
    max_results_per_source: int = 5,
    year: str | None = None,
    search_mode: Literal["keyword", "semantic"] = "keyword",
    verdict: Literal["supported", "refuted", "inconclusive"] | None = None,
    stage: Literal["prereg", "results"] | None = None,
) -> dict[str, Any]:
    """Search academic papers across multiple sources in parallel.

    Sources: openalex, semantic_scholar, arxiv, airas_db (curated conference
    database: the major ML and NLP venues, plus the formal-methods and
    theorem-proving venues — ITP, CPP, CADE, IJCAR, CAV, TACAS, LICS, POPL —
    for theory claims), airas_records (the research AIRAS itself produced
    whose gate passed). Pass a comma-separated subset or "all". `year`
    filters by publication year ("2024" or "2020-2024"); it does not apply
    to airas_records.

    `airas_records` matches the query against what each study hypothesized
    and claimed — and the titles of the papers it built on, so a paper's
    title finds the studies that rest on it — not against paper prose. Each
    row's `abstract` lists the hypotheses and claims with their verdicts, and
    `external_ids.airas_record` is the id `register_sources` takes. `verdict`
    keeps studies with a claim of that verdict (`refuted` finds what has
    already failed), `stage` keeps preregistered-only or realized studies;
    both apply to airas_records alone, so select only that source with them.

    `search_mode="keyword"` (default) does lexical/relevance search on every
    source. `search_mode="semantic"` does AI-embedding search that matches by
    meaning; it is only supported by `openalex` and requires OPENALEX_API_KEY
    (so pass sources="openalex"). Selecting any other source in semantic mode
    is an error.

    Results are normalized (title, authors, abstract, doi, arxiv_id, pdf_url,
    citations, source) and de-duplicated across sources; failures of
    individual sources are reported in `search_errors` without failing the
    search. Keyword search needs no API keys (SEMANTIC_SCHOLAR_API_KEY /
    OPENALEX_API_KEY optionally raise rate limits). Pass promising titles to
    `retrieve_papers`, or an arxiv_id / doi / pdf_url to
    `fetch_paper_fulltext`.
    """
    refresh_environment()
    if search_mode == "semantic" and not os.getenv("OPENALEX_API_KEY"):
        raise RuntimeError(
            f"Semantic search requires OPENALEX_API_KEY. {SETUP_INSTRUCTIONS}"
        )
    result = await search_papers_usecase.search_papers(
        query,
        sources=search_papers_usecase.parse_sources(sources),
        max_results_per_source=max_results_per_source,
        year=year,
        search_mode=search_mode,
        verdict=verdict,
        stage=stage,
        openalex_client=_openalex_client(),
        semantic_scholar_client=_semantic_scholar_client(),
        arxiv_client=_arxiv_client(),
        airas_db_index=_search_index,
        airas_records_index=_records_index,
    )
    return {
        "papers": [paper.model_dump(exclude_none=True) for paper in result["papers"]],
        "source_results": result["source_results"],
        "search_errors": result["search_errors"],
    }


@mcp.tool()
async def fetch_paper_fulltext(
    arxiv_id: str | None = None,
    doi: str | None = None,
    pdf_url: str | None = None,
    max_chars: int | None = 40000,
) -> dict[str, Any]:
    """Fetch the full text of a paper by arXiv ID, DOI, or direct PDF URL.

    Identifiers are tried in the order arXiv ID, then PDF URL, then DOI, and
    passing several is useful rather than wasteful: arXiv IDs are fetched
    straight from arXiv, DOIs are resolved to an open-access PDF through
    Semantic Scholar, and a DOI that resolves to nothing falls back to the
    `pdf_url` you supplied. Pass both whenever `search_papers` gave you both
    — a DOI alone returns only the abstract for any paper Semantic Scholar's
    open-access index does not cover, bioRxiv among them.

    Returns the extracted text with `status`: "fulltext", "abstract_only"
    (no open-access PDF found, abstract returned instead), or "not_found".

    A paper can run to 80k+ characters, so the text is capped at `max_chars`
    — **characters, not tokens**, default 40000 — with `total_chars`
    reporting the full length and `truncated` saying whether anything was
    cut. There is no paging: raising the cap re-fetches the paper from the
    start. Neither MCP nor this server imposes a size limit; the cap exists
    because reading a few uncapped papers exhausts a context window, and
    because a client may divert an oversized result to a file. The default
    assumes English prose at roughly four characters per token — lower it
    explicitly for CJK text, where a character is closer to a token.
    No API keys required.
    """
    if not (arxiv_id or doi or pdf_url):
        raise ValueError("One of arxiv_id, doi, or pdf_url must be provided.")
    refresh_environment()
    result = (
        await FetchPaperFulltextSubgraph(
            semantic_scholar_client=_semantic_scholar_client(),
        )
        .build_graph()
        .ainvoke(
            {
                "arxiv_id": arxiv_id,
                "doi": doi,
                "pdf_url": pdf_url,
                "max_chars": max_chars,
            }
        )
    )
    return {
        "text": result["text"],
        "status": result["status"],
        "resolved_from": result["resolved_from"],
        "total_chars": result["total_chars"],
        "truncated": result["truncated"],
    }


@mcp.tool()
async def retrieve_papers(paper_titles: list[str], model: str) -> list[dict[str, Any]]:
    """Retrieve full paper information for the given titles.

    Fetches each paper (via arXiv) and extracts structured research study
    data: abstract, methods, experimental settings, and results. The returned
    objects can be passed to `generate_hypothesis` as `research_study_list`.
    `model` (required) is the LLM to use — call `get_available_llms` to list
    valid models. Requires GH_PERSONAL_ACCESS_TOKEN and an LLM provider API key.
    """
    result = (
        await RetrievePaperSubgraph(
            litellm_client=_litellm_client(),
            arxiv_client=_arxiv_client(),
            github_client=_github_client(),
            llm_mapping=uniform_llm_mapping(RetrievePaperSubgraphLLMMapping, model),
        )
        .build_graph()
        .ainvoke({"paper_titles": paper_titles})
    )
    return [study.model_dump() for study in result["research_study_list"]]


@mcp.tool()
async def generate_hypothesis(
    research_topic: str,
    research_study_list: list[dict[str, Any]],
    model: str,
    refinement_rounds: int = 1,
) -> dict[str, Any]:
    """Generate a novel research hypothesis from a topic and related studies (backend LLM).

    `research_study_list` should be the output of `retrieve_papers`. Higher
    `refinement_rounds` improves quality at the cost of more LLM calls.
    `model` (required) is the LLM to use — call `get_available_llms` to list
    valid models. Requires an LLM provider API key — without one, use
    `get_generation_prompt(step="hypothesis", ...)` and author the
    hypothesis yourself.
    """
    studies = [ResearchStudy.model_validate(study) for study in research_study_list]
    result = (
        await GenerateHypothesisSubgraphV0(
            litellm_client=_litellm_client(),
            refinement_rounds=refinement_rounds,
            llm_mapping=uniform_llm_mapping(
                GenerateHypothesisSubgraphV0LLMMapping, model
            ),
        )
        .build_graph()
        .ainvoke(
            {
                "research_topic": research_topic,
                "research_study_list": studies,
            }
        )
    )
    return result["research_hypothesis"].model_dump()
