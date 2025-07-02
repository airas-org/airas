# ruff: noqa: E402
from fastmcp import FastMCP

from airas.services.mcp_server.mcp_tools.create_mcp_tool import (
    create_mcp_tool as create_mcp_tool_logic,
)

# Initialize FastMCP server
mcp: FastMCP = FastMCP("airas")


@mcp.tool(
    description="Given a Python module path, this tool reads the source code, generates a corresponding MCP tool using an LLM, saves it to the appropriate directory, and automatically registers it to the MCP server."
)
async def create_mcp_tool(
    module_path: str,
) -> str | None:
    """
    Automatically generate and register an MCP-compatible tool using a language model.

    This tool takes the module path of a Python subgraph implementation, loads its source code,
    sends it to an LLM using a Jinja2 template prompt, and automatically registers a FastMCP-compatible tool into the MCP server.

    Args:
        module_path (str): The importable Python module path of the subgraph.

    Returns:
        str: A success message with the file path if the tool was created successfully,
             or an error message if the generation failed.
    """
    result = create_mcp_tool_logic(module_path)
    return result


# -------------------- MCP Tool Registration --------------------
# All new MCP-compatible tools should be added **below this line**.
# Each MCP tool must accept a single input argument named `state`.


from airas.features.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph import (
    RetrievePaperFromQuerySubgraph,
)


@mcp.tool(
    description="This tool takes a state dictionary containing a 'base_queries' field, processes it through a paper retrieval subgraph that performs web scraping, arXiv searching, paper text extraction, GitHub URL extraction, and summarization, and finally selects the best paper. The output state includes a 'base_github_url' and 'base_method_text' representing the selected paper details."
)
def retrieve_paper_from_query_subgraph(state: dict) -> dict:
    state = RetrievePaperFromQuerySubgraph(
        llm_name="o3-mini-2025-01-31",
        save_dir="/workspaces/airas/data",
        scrape_urls=["https://icml.cc/virtual/2024/papers.html?filter=title"],
    ).run(state)
    return state


from airas.features.retrieve.retrieve_related_paper_subgraph.retrieve_related_paper_subgraph import (
    RetrieveRelatedPaperSubgraph,
)


@mcp.tool(
    description="This tool takes a state dictionary that includes 'base_queries', 'base_github_url', 'base_method_text', and optionally 'add_queries'. It instantiates the RetrieveRelatedPaperSubgraph with fixed configuration parameters (using 'o3-mini-2025-01-31' as the LLM name, '/workspaces/airas/data' as the save directory, a preset scrape URL, and an add paper number of 1) to run the related paper retrieval process, and returns the updated state."
)
def retrieve_related_paper_subgraph(state: dict) -> dict:
    state = RetrieveRelatedPaperSubgraph(
        llm_name="o3-mini-2025-01-31",
        save_dir="/workspaces/airas/data",
        scrape_urls=["https://icml.cc/virtual/2024/papers.html?filter=title"],
        add_paper_num=1,
    ).run(state)
    return state


from airas.features.retrieve.retrieve_code_subgraph.retrieve_code_subgraph import (
    RetrieveCodeSubgraph,
)


@mcp.tool(
    description="This tool takes a state dictionary with 'base_github_url' and 'base_method_text' fields, instantiates the RetrieveCodeSubgraph with a predefined LLM model, runs the subgraph to retrieve repository content and extract experimental code and info, and returns the updated state containing 'repository_content_str', 'base_experimental_code', and 'base_experimental_info'."
)
def retrieve_code_subgraph(state: dict) -> dict:
    state = RetrieveCodeSubgraph().run(state)
    return state


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    mcp.run(transport="stdio")
