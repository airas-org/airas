from jinja2 import Environment
from pydantic import BaseModel

from airas.core.llm_config import NodeLLMConfig
from airas.infra.langchain_client import LangChainClient

# def _build_generated_query_model(n_queries: int) -> type[BaseModel]:
#     fields = {f"generated_query_{i + 1}": (str, ...) for i in range(n_queries)}
#     return create_model("LLMOutput", **fields)


class LLMOutput(BaseModel):
    query_list: list[str]


async def generate_queries(
    llm_config: NodeLLMConfig,
    llm_client: LangChainClient,
    prompt_template: str,
    research_topic: str,
    num_paper_search_queries: int,
) -> list[str]:
    data = {
        "research_topic": research_topic,
        "n_queries": num_paper_search_queries,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    # DynamicLLMOutput = _build_generated_query_model(num_paper_search_queries)
    output = await llm_client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
        llm_name=llm_config.llm_name,
        params=llm_config.params,
    )
    if output is None:
        raise ValueError("Error: No response from LLM in generate_queries_node.")

    return output.query_list
