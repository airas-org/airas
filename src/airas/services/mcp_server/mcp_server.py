from fastmcp import FastMCP

from airas.services.mcp_server.mcp_tools.create_mcp_tool import (
    create_mcp_tool as create_mcp_tool_logic,
)

# Initialize FastMCP server
mcp: FastMCP = FastMCP("airas")


@mcp.tool()
async def create_mcp_tool(
    module_path: str,
) -> str:
    """
    Automatically generate and register an MCP-compatible tool using a language model.

    This tool takes the module path of a Python subgraph implementation, loads its source code,
    sends it to an LLM using a Jinja2 template prompt, and automatically generates, saves,
    and registers a FastMCP-compatible tool into the MCP server.

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

from airas.services.mcp_server.mcp_tools.retrieve_paper_from_query_subgraph_mcp import (  # noqa: E402
    retrieve_paper_from_query_subgraph_mcp,
)


@mcp.tool(
    description="This tool accepts a state dictionary containing a list of base_queries, initializes the RetrievePaperFromQuerySubgraph with server configuration parameters (llm_name, save_dir, and scrape_urls), executes the subgraph to retrieve paper information, and returns a human-readable summary containing the base GitHub URL and details of the selected paper."
)
def retrieve_paper_from_query_subgraph(state: dict) -> str:
    return retrieve_paper_from_query_subgraph_mcp(state)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    mcp.run(transport="stdio")
