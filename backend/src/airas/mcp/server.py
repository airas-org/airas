from airas.mcp import prompts, tools
from airas.mcp.app import mcp

__all__ = ["main", "mcp", "prompts", "tools"]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
