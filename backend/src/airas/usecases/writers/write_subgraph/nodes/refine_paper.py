from jinja2 import Environment

from airas.core.types.paper import PaperContent
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS
from airas.usecases.writers.write_subgraph.prompts.refine_prompt import refine_prompt
from airas.usecases.writers.write_subgraph.prompts.section_tips_prompt import (
    section_tips_prompt,
)
from airas.usecases.writers.write_subgraph.prompts.write_prompt import write_prompt


async def refine_paper(
    llm_name: LLM_MODELS,
    langchain_client: LangChainClient,
    paper_content: PaperContent,
    note: str,
) -> PaperContent:
    env = Environment()
    write_prompt_template = env.from_string(write_prompt)
    rendered_system_prompt = write_prompt_template.render(
        note=note,
        tips_dict=section_tips_prompt,
    )

    refine_prompt_template = env.from_string(refine_prompt)
    refine_message = refine_prompt_template.render(content=paper_content)

    messages = rendered_system_prompt + refine_message

    output = await langchain_client.structured_outputs(
        message=messages, data_model=PaperContent, llm_name=llm_name
    )
    if output is None:
        raise ValueError("Error: No response from LLM in refine_paper.")

    return output
