"""Every AIRAS MCP tool, grouped by what it does.

Importing a module here is what registers its tools on the shared
``mcp`` instance.
"""

from airas.mcp.tools import (
    capabilities,
    design,
    discovery,
    execution,
    figures,
    history,
    publication,
    record,
    repository,
    reproduction,
)

__all__ = [
    "capabilities",
    "design",
    "discovery",
    "execution",
    "figures",
    "history",
    "publication",
    "record",
    "repository",
    "reproduction",
]
