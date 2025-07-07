import asyncio
import importlib.util
from logging import getLogger

from fastmcp import Client

logger = getLogger(__name__)


def get_mcp_server_path() -> str:
    module_name = "airas.services.mcp_server.mcp_server"
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None or spec.origin is None:
            raise FileNotFoundError(
                f"Could not find the file for '{module_name}' module."
            )

        logger.info(f"Dynamically resolved MCP server path: {spec.origin}")
        return spec.origin

    except (ModuleNotFoundError, FileNotFoundError) as e:
        logger.error(f"Failed to dynamically determine MCP server path: {e}")
        logger.error(
            "Please ensure the 'airas' project is installed correctly (e.g., 'pip install -e .') "
            "or that the project's 'src' directory is in PYTHONPATH."
        )


mcp_server_path = get_mcp_server_path()
client: Client = Client(mcp_server_path)


async def call_tool(tool_name: str, input: dict) -> str:
    async with client:
        return await client.call_tool(tool_name, input)


if __name__ == "__main__":
    input = {"state": {"base_queries": ["transformer"]}}
    result = asyncio.run(call_tool("retrieve_paper_from_query_subgraph", input))
    print(result)
