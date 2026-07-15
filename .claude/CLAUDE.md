# CLAUDE.md
@.claude/CLAUDE.local.md

An OSS toolkit for research automation. The primary interface is a local MCP server (`airas-mcp`, stdio); an optional web dashboard (React frontend + FastAPI backend) can also be launched. No database is used.

# Module Structure

- `backend/`: Backend code implemented in Python (FastAPI)
- `frontend/`: Frontend code implemented in TypeScript + React (Vite)
- `docs/`: Documentation site implemented in Markdown (Mintlify)
