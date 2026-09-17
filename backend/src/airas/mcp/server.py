from airas.mcp import tools
from airas.mcp.app import mcp

__all__ = ["main", "mcp", "tools"]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
