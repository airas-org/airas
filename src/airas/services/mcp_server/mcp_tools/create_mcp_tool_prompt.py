create_mcp_tool_prompt = """
You are an expert Python engineer.

**MCP stands for Model Context Protocol.**  
The goal is to enable the function to be used via a FastMCP server.

---

## Tool specification:

- Module path: `{{ module_path }}`

---

## Instructions:

- Output only valid Python code.
- Use the actual Subgraph class name found in the `source_code` when importing and instantiating the subgraph.
- The function must:
  - Take a single argument named `state` (a dictionary)
  - Operate on fields inside `state`
  - Return the final `state` as-is
- Include a clear and concise natural-language description inside `@mcp.tool(description="...")`, summarizing:
  - what the tool takes as input (Use actual key names present in the `state` object)
  - what it does
  - what it returns  

- **Do not insert any blank line between `@mcp.tool(...)` and the `def` line.** The decorator must be immediately followed by the function definition without any newline in between.
- Function name: use the **last part** of the `module_path`.

- Refer to the `main()` function in the `source_code` to determine:
  - How to instantiate the Subgraph (e.g., which arguments to pass, such as fixed values or config variables)
  - How to structure the input `state` (i.e., required fields and example values)
- Do not extract constructor arguments from `state`.
- You may omit arguments that have default values in the class definition.
  
- Do not add any:
  - Extra imports 
  - Helper functions
  - Anything outside what's in the Reference template

---

## Output format:

Return a JSON object **as a string** with exactly one field:
- `output_code`: A complete implementation of the MCP-compatible tool, following the structure shown in the reference template.

---

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
