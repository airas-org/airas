from jinja2 import Environment
from airas.utils.api_client.llm_facade_client import LLMFacadeClient, LLM_MODEL
from airas.create.create_method_subgraph.prompt.generator_node_prompt import (
    generator_node_prompt,
)
from logging import getLogger

logger = getLogger(__name__)


def generator_node(
    llm_name: LLM_MODEL,
    base_method_text: str,
    add_method_text_list: list[str],
) -> str:
    client = LLMFacadeClient(llm_name)

    add_method_text = "---".join(add_method_text_list)
    env = Environment()
    template = env.from_string(generator_node_prompt)
    data = {
        "base_method_text": base_method_text,
        "add_method_text": add_method_text,
    }
    messages = template.render(data)
    output, cost = client.generate(
        message=messages,
    )
    if output is None:
        raise ValueError("Error: No response from the model in generator_node.")
    return output


if __name__ == "__main__":
    llm_name = "o3-mini-2025-01-31"
    base_method_text = "test"
    add_method_text_list = "test"
    output = generator_node(
        llm_name=llm_name,
        base_method_text=base_method_text,
        add_method_text_list=add_method_text_list,
    )
    print(output)
