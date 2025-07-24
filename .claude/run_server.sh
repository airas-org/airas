JSON_PAYLOAD=$(printf '{
  "type": "stdio",
  "command": "uv",
  "args": [
    "run",
    "python",
    "%s/src/airas/services/mcp_server/mcp_server.py"
  ]
}' "$PWD")

claude mcp add-json airas "$JSON_PAYLOAD"