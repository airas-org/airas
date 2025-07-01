create_mcp_tool_prompt = """
You are an expert Python engineer.

**MCP stands for Model Context Protocol.**  
The goal is to enable the function to be used via a FastMCP server.

## Tool specification:

- Module path: `{{ module_path }}`
- MCP tool name: `{{ tool_name }}`

## Instructions:

- Output only valid Python code.
- Use `from {{ module_path }} import ...` for imports. Do not change, shorten, or omit the `module_path`.
- Format return values using a helper like `format_result()` based on the actual structure of `state`.
- **Read the `source_code` and infer:**
    - The appropriate arguments required to instantiate the Subgraph class.
    - How to define `MCPServerConfig` with the necessary attributes to support subgraph instantiation.
    - How the final state looks, in order to design `format_result()` for human-readability.
- Do not include explanations or comments outside of the code block.

- Finally, return a JSON object with:
  - `description`: A brief natural language summary describing what the tool takes as input, what it does, and what it returns.
  - `output_code`: The full code of the MCP-compatible tool

## Source code of the module:

Below is the full code of the source module. You can use it to understand class definitions, subgraph initialization, helper functions like `format_result`, and server-level configs like `MCPServerConfig`.

```python
{{ source_code | indent(4) }}


## Reference template:

```python
from your_module_path import (
    YourSubgraph,
)

class MCPServerConfig:
    def __init__(self, **kwargs):
        self.config1 = kwargs.get("config1")
        self.config2 = kwargs.get("config2")

server_config = MCPServerConfig(
    config1=...,
    config2=...,
)

def format_result(state) -> str:
    return f"Result:\n{state}"


def {{ tool_name }}_mcp(state: dict) -> str:
    subgraph = YourSubgraph(
        config1=server_config.config1,
        config2=server_config.config2,
    )

    state = subgraph.run(state, config={"recursion_limit": 500})
    return format_result(state)
```
"""
