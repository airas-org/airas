## How to Use the MCP Server in AIRAS

- Each subgraph in AIRAS can be used as an MCP tool via VSCode.
The MCP server configuration file is located at `.vscode/mcp.json`.

- To start the MCP server, run:
```bash
uv run python path/to/your/repo/src/airas/services/mcp_server/mcp_server.py
```
- Once the server is running, GitHub Copilot can interact with the registered subgraphs as MCP tools.

- To add a new MCP tool, you can use the `create_mcp_tool`, which is itself available as an MCP tool.
By providing the target module path, it will automatically generate and register the tool on the server.

Note: After adding a new tool, please restart the MCP server to make it available.