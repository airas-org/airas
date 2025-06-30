from airas.features.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph import (
    RetrievePaperFromQuerySubgraph,
)


class MCPServerConfig:
    def __init__(
        self,
        llm_name,
        save_dir,
        scrape_urls,
        arxiv_query_batch_size=10,
        arxiv_num_retrieve_paper=1,
        arxiv_period_days=None,
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.scrape_urls = scrape_urls
        self.arxiv_query_batch_size = arxiv_query_batch_size
        self.arxiv_num_retrieve_paper = arxiv_num_retrieve_paper
        self.arxiv_period_days = arxiv_period_days


server_config = MCPServerConfig(
    llm_name="o3-mini-2025-01-31",
    save_dir="/workspaces/airas/data",
    scrape_urls=[
        "https://icml.cc/virtual/2024/papers.html?filter=title",
    ],
    arxiv_query_batch_size=10,
    arxiv_num_retrieve_paper=1,
    arxiv_period_days=None,
)


def format_result(state) -> str:
    result = "Result:\n"
    result += f"Base GitHub URL: {state.get('base_github_url', 'N/A')}\n"
    base_method_text = state.get("base_method_text", {})
    if isinstance(base_method_text, dict):
        result += "Paper Info:\n"
        result += f"  Title: {base_method_text.get('title', 'N/A')}\n"
        result += f"  Authors: {base_method_text.get('authors', 'N/A')}\n"
        result += f"  Summary: {base_method_text.get('summary', 'N/A')}\n"
        result += f"  Arxiv ID: {base_method_text.get('arxiv_id', 'N/A')}\n"
    else:
        result += f"{base_method_text}\n"
    return result


def retrieve_paper_from_query_subgraph_mcp(state: dict) -> str:
    subgraph = RetrievePaperFromQuerySubgraph(
        llm_name=server_config.llm_name,
        save_dir=server_config.save_dir,
        scrape_urls=server_config.scrape_urls,
        arxiv_query_batch_size=server_config.arxiv_query_batch_size,
        arxiv_num_retrieve_paper=server_config.arxiv_num_retrieve_paper,
        arxiv_period_days=server_config.arxiv_period_days,
    )
    state = subgraph.run(state, config={"recursion_limit": 500})
    return format_result(state)
