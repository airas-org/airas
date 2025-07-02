create_mcp_tool_prompt = """
You are an expert Python engineer.

**MCP stands for Model Context Protocol.**  
The goal is to enable the function to be used via a FastMCP server.

## Tool specification:

- Module path: `{{ module_path }}`

## Instructions:

- Output only valid Python code.
- Use the actual Subgraph class name found in the source_code when importing and instantiating the subgraph.
- Include a clear and concise natural-language description inside `@mcp.tool(description="...")`, summarizing what the tool takes as input, what it does, and what it returns.  
  The function must always take a single argument named `state`, and the actual input values are provided as fields inside this `state` dictionary.
- Name the tool function using the last part of the `module_path`.
- Read the `source_code` to infer the arguments needed to instantiate the Subgraph class.
  In particular, do not extract constructor arguments from state. Instead, refer to the main() function in the source code to determine how the Subgraph is instantiated, using fixed values or configuration variables. 
  You may omit arguments that have default values in the class definition.
- Return the final `state` as-is from the function.
- Do not add any imports or helper functions that are not already shown in the Reference template.

- Return a JSON object **as a string** with exactly one field:
  - `output_code`: A complete implementation of the MCP-compatible tool, following the structure shown in the reference template.

## Source code of the module:

Below is the full code of the source module. You can use it to understand class definitions, subgraph initialization.

```python
{{ source_code | indent(4) }}


## Reference template:

```python
from {{ module_path }} import (
    YourSubgraph,
)

@mcp.tool(description="Brief explanation of what the tool does.")
def your_subgraph(state: dict) -> dict:
    state = YourSubgraph(
        # appropriate arguments
    ).run(state)

    return state
```
"""
