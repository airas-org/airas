import asyncio

from fastmcp import Client

client: Client = Client("/workspaces/airas/src/airas/services/mcp_server/mcp_server.py")


async def call_tool(tool_name: str, input: dict) -> str:
    async with client:
        return await client.call_tool(tool_name, input)


if __name__ == "__main__":
    input = {"state": {"base_queries": ["transformer"]}}
    result = asyncio.run(call_tool("retrieve_paper_from_query_subgraph", input))
    print(result)
