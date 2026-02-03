from jinja2 import Environment
from airas.core.llm_config import NodeLLMConfig
from airas.core.types.paper import BasePaperContent, PaperContent
from airas.infra.langchain_client import LangChainClient


async def write_paper(
    llm_config: NodeLLMConfig,
    langchain_client: LangChainClient,
    note: str,
    prompt_template: str,
    section_tips_prompt: dict[str, str],
    paper_content_model: type[BasePaperContent],
    prompt_prefix: str | None = None,
) -> PaperContent:
    env = Environment()
    template = env.from_string(prompt_template)
    if prompt_prefix:
        context = {
            f"{prompt_prefix}_note": note,
            f"{prompt_prefix}_tips_dict": section_tips_prompt,
        }
    else:
        context = {
            "note": note,
            "tips_dict": section_tips_prompt,
        }
    messages = template.render(context)

    output = await langchain_client.structured_outputs(
        message=messages,
        data_model=paper_content_model,
        llm_name=llm_config.llm_name,
        params=llm_config.params,
    )
    if output is None:
        raise ValueError("Error: No response from LLM in write_paper.")

    return output
