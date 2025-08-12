from jinja2 import Environment
from pydantic import BaseModel, create_model

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)


def _build_generated_query_model(n_queries: int) -> type[BaseModel]:
    fields = {f"generated_query_{i + 1}": (str, ...) for i in range(n_queries)}
    return create_model("LLMOutput", **fields)


def generate_queries(
    llm_name: LLM_MODEL,
    prompt_template: str,
    research_topic: str,
    n_queries: int,
    client: LLMFacadeClient | None = None,
) -> list[str]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {
        "research_topic": research_topic,
        "n_queries": n_queries,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    DynamicLLMOutput = _build_generated_query_model(n_queries)
    output, cost = client.structured_outputs(
        message=messages, data_model=DynamicLLMOutput
    )
    if output is None:
        raise ValueError("Error: No response from LLM in generate_queries_node.")

    return [output[f"generated_query_{i + 1}"] for i in range(n_queries)]
