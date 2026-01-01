from jinja2 import Environment
from pydantic import BaseModel, create_model

from airas.services.api_client.llm_client.llm_facade_client import (
    LLMFacadeClient,
)
from airas.services.api_client.llm_specs import LLM_MODELS


def _build_generated_query_model(n_queries: int) -> type[BaseModel]:
    fields = {f"generated_query_{i + 1}": (str, ...) for i in range(n_queries)}
    return create_model("LLMOutput", **fields)


async def generate_queries(
    llm_name: LLM_MODELS,
    llm_client: LLMFacadeClient,
    prompt_template: str,
    research_topic: str,
    n_queries: int,
) -> list[str]:
    data = {
        "research_topic": research_topic,
        "n_queries": n_queries,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    DynamicLLMOutput = _build_generated_query_model(n_queries)
    output = await llm_client.structured_outputs(
        message=messages, data_model=DynamicLLMOutput, llm_name=llm_name
    )
    if output is None:
        raise ValueError("Error: No response from LLM in generate_queries_node.")

    return [output[f"generated_query_{i + 1}"] for i in range(n_queries)]
