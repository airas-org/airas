---
title: MCP
slug: /development/MCP
---

# MCP Server

AIRAS provides a local MCP (Model Context Protocol) server that exposes research subgraphs as tools for MCP clients such as Claude Code and Claude Desktop.

## Setup

No installation is required — `uvx` fetches the package on first run. The only prerequisite is [uv](https://docs.astral.sh/uv/).

### Claude Code

```bash
claude mcp add airas \
  --env OPENAI_API_KEY=sk-... \
  --env GH_PERSONAL_ACCESS_TOKEN=ghp_... \
  -- uvx --from "airas[mcp]" airas-mcp
```

Or add it to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "airas": {
      "command": "uvx",
      "args": ["--from", "airas[mcp]", "airas-mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "GH_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
```

### Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | At least one | LLM calls (query generation, paper extraction, hypothesis generation) |
| `GH_PERSONAL_ACCESS_TOKEN` | For `retrieve_papers` | GitHub API access |

## Tools

| Tool | Description |
| --- | --- |
| `generate_research_queries` | Generate paper search queries from a research topic |
| `search_paper_titles` | BM25 search over the AIRAS papers database (major ML conferences); no API key required |
| `retrieve_papers` | Fetch papers via arXiv and extract structured research study data |
| `generate_hypothesis` | Generate a novel research hypothesis from a topic and related studies |

A typical flow: `generate_research_queries` → `search_paper_titles` → `retrieve_papers` → `generate_hypothesis`.

## Development

Run the server from a checkout:

```bash
cd backend
uv sync --extra mcp
uv run airas-mcp
```

The server uses stdio transport; it is started on demand by the MCP client and requires no database or web server.
