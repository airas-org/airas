import importlib.util
from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.services.mcp_server.mcp_tools.create_mcp_tool_prompt import (
    create_mcp_tool_prompt,
)

logger = getLogger(__name__)


BASE_DIR = "/workspaces/airas"
MCP_SERVER_PATH = f"{BASE_DIR}/src/airas/services/mcp_server/mcp_server.py"


class LLMOutput(BaseModel):
    output_code: str


def _module_path_to_file_content(module_path: str) -> str:
    spec = importlib.util.find_spec(module_path)
    if spec is None or spec.origin is None:
        raise FileNotFoundError(f"Module {module_path} not found")
    with open(spec.origin, encoding="utf-8") as f:
        return f.read()


def _update_mcp_server(code: str, mcp_server_path: str) -> bool:
    try:
        with open(mcp_server_path, encoding="utf-8") as f:
            lines = f.readlines()

        insert_index = None
        for i, line in enumerate(lines):
            if line.strip().startswith("if __name__ =="):
                insert_index = i
                break

        if insert_index is None:
            logger.error("`if __name__ == '__main__'` block not found in mcp_server.py")
            return False

        if code.strip() in "".join(lines):
            logger.warning("Code block already exists in mcp_server.py")
            return False

        formatted_code = code.strip("\n") + "\n\n"
        lines.insert(insert_index, formatted_code)

        with open(mcp_server_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        logger.info(f"Appended MCP tool function to {mcp_server_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to register tool in mcp_server.py: {e}")
        return False


def create_mcp_tool(
    module_path: str,
    *,
    llm_name: LLM_MODEL = "o3-mini-2025-01-31",
    mcp_server_path: str = MCP_SERVER_PATH,
    client: LLMFacadeClient | None = None,
) -> str | None:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    try:
        source_code = _module_path_to_file_content(module_path)
    except Exception as e:
        logger.error(f"Failed to load source code for module {module_path}: {e}")
        return None

    env = Environment()
    messages = env.from_string(create_mcp_tool_prompt).render(
        {
            "module_path": module_path,
            "source_code": source_code,
        }
    )

    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        logger.error("Error: No response from LLM.")
        return None

    output_code = output["output_code"]

    return _update_mcp_server(output_code, mcp_server_path)


if __name__ == "__main__":
    result = create_mcp_tool(
        module_path="airas.features.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph",
    )
