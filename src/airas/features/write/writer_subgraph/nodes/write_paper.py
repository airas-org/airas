from jinja2 import Environment

from airas.features.write.writer_subgraph.prompt.section_tips_prompt import (
    section_tips_prompt,
)
from airas.features.write.writer_subgraph.prompt.write_prompt import write_prompt
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent


async def write_paper(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
    note: str,
) -> PaperContent:
    env = Environment()
    template = env.from_string(write_prompt)
    messages = template.render(
        note=note,
        tips_dict=section_tips_prompt,
    )

    output, cost = await llm_client.structured_outputs(
        message=messages, data_model=PaperContent, llm_name=llm_name
    )
    if output is None:
        raise ValueError("Error: No response from LLM in write.")

    missing_fields = [
        field
        for field in PaperContent.model_fields
        if field not in output or not output[field].strip()
    ]
    if missing_fields:
        raise ValueError(f"Missing or empty fields in model response: {missing_fields}")

    return PaperContent(**output)
