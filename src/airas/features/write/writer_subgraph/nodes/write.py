from jinja2 import Environment

from airas.features.write.writer_subgraph.prompt.section_tips_prompt import (
    section_tips_prompt,
)
from airas.features.write.writer_subgraph.prompt.system_prompt import system_prompt
from airas.features.write.writer_subgraph.prompt.write_prompt import write_prompt
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent


def write(
    llm_name: LLM_MODEL,
    note: str,
    client: LLMFacadeClient | None = None,
) -> dict[str, str]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(system_prompt)
    rendered_system_prompt = template.render(
        note=note,
        tips_dict=section_tips_prompt,
    )

    messages = rendered_system_prompt + write_prompt

    output, cost = client.structured_outputs(message=messages, data_model=PaperContent)
    if output is None:
        raise ValueError("Error: No response from LLM in write.")

    missing_fields = [
        field
        for field in PaperContent.model_fields
        if field not in output or not output[field].strip()
    ]
    if missing_fields:
        raise ValueError(f"Missing or empty fields in model response: {missing_fields}")

    return output
