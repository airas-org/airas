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

from airas.services.mcp_server.mcp_tools.retrieve_paper_from_query_subgraph_mcp import (
    retrieve_paper_from_query_subgraph_mcp,
)


@mcp.tool(
    description="This MCP tool takes a state dictionary as input containing a list of base queries. It instantiates the RetrievePaperFromQuerySubgraph with server configuration parameters (LLM name, data directory, and URLs to scrape) and then runs the subgraph to retrieve and process academic papers. The final state is formatted to display the base GitHub URL and the associated method text details."
)
def retrieve_paper_from_query_subgraph(state: dict) -> str:
    return retrieve_paper_from_query_subgraph_mcp(state)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    mcp.run(transport="stdio")
