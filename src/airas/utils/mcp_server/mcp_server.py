from typing import List

from mcp.server.fastmcp import FastMCP
from airas.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
    RetrievePaperInputState,
)

# Initialize FastMCP server
mcp = FastMCP("research-graph")


class MCPServerConfig:
    def __init__(self, save_dir: str, scrape_urls: List[str], add_paper_num: int):
        self.save_dir = save_dir
        self.scrape_urls: List[str] = scrape_urls
        self.add_paper_num = add_paper_num


server_config = MCPServerConfig(
    save_dir="./data",
    scrape_urls=[
        "https://icml.cc/virtual/2024/papers.html?filter=title",
        "https://iclr.cc/virtual/2024/papers.html?filter=title",
        # "https://nips.cc/virtual/2024/papers.html?filter=title",
        # "https://cvpr.thecvf.com/virtual/2024/papers.html?filter=title",
        # "https://eccv.ecva.net/virtual/2024/papers.html?filter=title",
    ],
    add_paper_num=3,
)


def format_search_results(state) -> str:
    def format_search_paper(paper):
        return "\n".join(
            [
                f"Title: {paper['title']}",
                f"Authors: {', '.join(paper['authors'])}",
                f"Summary: {paper['summary']}",
                f"Published: {paper['published_date']}",
                f"Link: {paper['arxiv_url']}",
            ]
        )

    def format_search_paper_list(papers):
        return "\n--\n".join(map(format_search_paper, papers))

    def format_selected_paper(paper):
        return "\n".join(
            [
                f"Title: {paper.title}",
                f"Authors: {', '.join(paper.authors)}",
                f"Summary: {paper.summary}",
                f"Contributions: {paper.main_contributions}",
                f"Experiments: {paper.experimental_setup}",
                f"Limitations: {paper.limitations}",
                f"Future Research Directions: {paper.future_research_directions}",
                f"Published: {paper.published_date}",
                f"Link: {paper.arxiv_url}",
            ]
        )

    return f"""
## Selected Base Paper
{format_selected_paper(state['selected_base_paper_info'])}

## Searched Papers
{format_search_paper_list(state['search_paper_list'])}
""".strip()


@mcp.tool()
async def retrieve_paper_subgraph(keywords: str) -> str:
    """
    Retrieve a subgraph of research papers based on the provided keywords.

    This function initializes a subgraph retrieval process using the specified
    keywords, builds a graph of related research papers, and formats the results
    for display. The search includes scraping paper metadata from configured URLs
    and processing them with a language model.

    Args:
        keywords (str): Comma-separated keywords to search for. Each keyword is
                        used to query and retrieve relevant research papers.

    Returns:
        str: A formatted string containing details of the selected base paper
             and a list of searched papers, including their titles, authors,
             summaries, publication dates, and links.
    """
    # Initialize the RetrievePaperSubgraph class
    subgraph = RetrievePaperSubgraph(
        llm_name="o3-mini-2025-01-31",
        save_dir=server_config.save_dir,
        scrape_urls=server_config.scrape_urls,
        add_paper_num=server_config.add_paper_num,
    ).build_graph()

    state: RetrievePaperInputState = RetrievePaperInputState(
        queries=list(map(lambda x: x.strip(), keywords.split(",")))
    )
    response = subgraph.invoke(state, config={"recursion_limit": 500})

    return format_search_results(response)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    mcp.run(transport="stdio")
