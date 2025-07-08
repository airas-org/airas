## How to Use the MCP Server in AIRAS
- Each subgraph in AIRAS can be used as an MCP tool in VSCode.
The MCP server configuration file is located at `.vscode/mcp.json`.

- To start the MCP server from the command line (CLI), run:
```bash
uv run python path/to/your/repo/src/airas/services/mcp_server/mcp_server.py
```
- If you are using **GitHub Copilot's Agent Mode** inside VSCode, 
  you can simply press the "Run" button inside `.vscode/mcp.json`.

- If you are using **Claude Code** and want to utilize the AIRAS MCP server,
  please execute the script below instead:
```bash
sh .claude/run_server.sh
```
Don't forget to grant execution permission to the script if needed: `chmod +x .claude/run_server.sh`

## Add a New MCP Tool
- You can use the `create_mcp_tool` (also available as an MCP tool) to add a new tool.
Just provide the target module path, and it will automatically register the tool on the server.

**Note:** After adding a new tool, please restart the MCP server to make it available.