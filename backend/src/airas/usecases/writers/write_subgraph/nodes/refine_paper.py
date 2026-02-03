from jinja2 import Environment
from airas.core.llm_config import NodeLLMConfig
from airas.core.types.paper import BasePaperContent, PaperContent
from airas.infra.langchain_client import LangChainClient


async def refine_paper(
    llm_config: NodeLLMConfig,
    langchain_client: LangChainClient,
    paper_content: PaperContent,
    note: str,
    write_prompt_template: str,
    refine_prompt_template: str,
    section_tips_prompt: dict[str, str],
    paper_content_model: type[BasePaperContent],
    prompt_prefix: str | None = None,
) -> PaperContent:
    env = Environment()
    write_prompt = env.from_string(write_prompt_template)
    prefix = f"{prompt_prefix}_" if prompt_prefix else ""
    write_context = {
        f"{prefix}note": note,
        f"{prefix}tips_dict": section_tips_prompt,
    }
    rendered_system_prompt = write_prompt.render(write_context)

    refine_prompt = env.from_string(refine_prompt_template)
    refine_context = {f"{prefix}content": paper_content}
    refine_message = refine_prompt.render(refine_context)

    messages = rendered_system_prompt + refine_message

    output = await langchain_client.structured_outputs(
        message=messages,
        data_model=paper_content_model,
        llm_name=llm_config.llm_name,
        params=llm_config.params,
    )
    if output is None:
        raise ValueError("Error: No response from LLM in refine_paper.")

    return output
