from jinja2 import Environment

from airas.features.writers.write_subgraph.prompts.section_tips_prompt import (
    section_tips_prompt,
)
from airas.features.writers.write_subgraph.prompts.write_prompt import write_prompt
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.types.paper import PaperContent


async def write_paper(
    llm_name: LLM_MODELS,
    langchain_client: LangChainClient,
    note: str,
) -> PaperContent:
    env = Environment()
    template = env.from_string(write_prompt)
    messages = template.render(
        note=note,
        tips_dict=section_tips_prompt,
    )

    output = await langchain_client.structured_outputs(
        message=messages, data_model=PaperContent, llm_name=llm_name
    )
    if output is None:
        raise ValueError("Error: No response from LLM in write_paper.")

    return output
