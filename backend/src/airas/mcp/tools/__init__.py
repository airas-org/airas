"""Every AIRAS MCP tool, grouped by what it does.

Importing a module here is what registers its tools on the shared
``mcp`` instance.
"""

from airas.mcp.tools import (
    capabilities,
    execution,
    figures,
    hypothesis_and_design,
    literature,
    publication,
    record,
    repository,
    reproduction,
)

__all__ = [
    "capabilities",
    "execution",
    "figures",
    "hypothesis_and_design",
    "literature",
    "publication",
    "record",
    "repository",
    "reproduction",
]
