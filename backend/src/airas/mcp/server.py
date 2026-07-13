"""AIRAS MCP server (stdio).

Exposes AIRAS research subgraphs as MCP tools for use from MCP clients
such as Claude Code and Claude Desktop.

Credentials are read from environment variables:
- LLM providers: OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY (at least one)
- GitHub (retrieve_papers only): GH_PERSONAL_ACCESS_TOKEN

Run locally:
    uvx --from "airas[mcp]" airas-mcp
"""

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from airas.core.types.research_study import ResearchStudy
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.usecases.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0,
)
from airas.usecases.generators.generate_queries_subgraph.generate_queries_subgraph import (
    GenerateQueriesSubgraph,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.search_paper_titles_from_airas_db_subgraph import (
    SearchPaperTitlesFromAirasDbSubgraph,
)

mcp = FastMCP("airas")

# BM25 index over the AIRAS papers DB; built lazily on first search and
# reused for the lifetime of the server process.
_search_index = AirasDbPaperSearchIndex()


def _github_client() -> GithubClient:
    token = os.getenv("GH_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError(
            "GH_PERSONAL_ACCESS_TOKEN environment variable is not set. "
            "Set it in the `env` block of your MCP client configuration."
        )
    return GithubClient(github_token=token)


@mcp.tool()
async def generate_research_queries(
    research_topic: str,
    num_queries: int = 2,
) -> list[str]:
    """Generate academic paper search queries from a research topic.

    Use this first to turn a free-form research topic into effective
    search queries, then pass them to `search_paper_titles`.
    """
    result = (
        await GenerateQueriesSubgraph(
            llm_client=LangChainClient(),
            num_paper_search_queries=num_queries,
        )
        .build_graph()
        .ainvoke({"research_topic": research_topic})
    )
    return result["queries"]


@mcp.tool()
async def search_paper_titles(
    queries: list[str],
    max_results_per_query: int = 3,
) -> list[str]:
    """Search the AIRAS papers database (major ML conferences) for paper titles.

    Takes search queries (e.g. from `generate_research_queries`) and returns
    matching paper titles. The first call builds the search index, which can
    take a while; subsequent calls are fast. No API keys required.
    """
    result = (
        await SearchPaperTitlesFromAirasDbSubgraph(
            search_index=_search_index,
            papers_per_query=max_results_per_query,
        )
        .build_graph()
        .ainvoke({"queries": queries})
    )
    return result["paper_titles"]


@mcp.tool()
async def retrieve_papers(paper_titles: list[str]) -> list[dict[str, Any]]:
    """Retrieve full paper information for the given titles.

    Fetches each paper (via arXiv) and extracts structured research study
    data: abstract, methods, experimental settings, and results. The returned
    objects can be passed to `generate_hypothesis` as `research_study_list`.
    Requires GH_PERSONAL_ACCESS_TOKEN and an LLM provider API key.
    """
    result = (
        await RetrievePaperSubgraph(
            langchain_client=LangChainClient(),
            arxiv_client=ArxivClient(),
            github_client=_github_client(),
            llm_mapping=None,
        )
        .build_graph()
        .ainvoke({"paper_titles": paper_titles})
    )
    return [study.model_dump() for study in result["research_study_list"]]


@mcp.tool()
async def generate_hypothesis(
    research_topic: str,
    research_study_list: list[dict[str, Any]],
    refinement_rounds: int = 1,
) -> dict[str, Any]:
    """Generate a novel research hypothesis from a topic and related studies.

    `research_study_list` should be the output of `retrieve_papers`. Higher
    `refinement_rounds` improves quality at the cost of more LLM calls.
    Requires an LLM provider API key.
    """
    studies = [ResearchStudy.model_validate(study) for study in research_study_list]
    result = (
        await GenerateHypothesisSubgraphV0(
            langchain_client=LangChainClient(),
            refinement_rounds=refinement_rounds,
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
