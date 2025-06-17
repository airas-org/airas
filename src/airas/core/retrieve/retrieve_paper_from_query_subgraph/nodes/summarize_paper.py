from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL, LLMFacadeClient


class LLMOutput(BaseModel):
    main_contributions: str
    methodology: str
    experimental_setup: str
    limitations: str
    future_research_directions: str


def summarize_paper(
    llm_name: LLM_MODEL,
    prompt_template: str,
    paper_text: str,
    client: LLMFacadeClient | None = None, 
) -> tuple[str, str, str, str, str]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    data = {
        "paper_text": paper_text,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)

    return (
        output["main_contributions"],
        output["methodology"],
        output["experimental_setup"],
        output["limitations"],
        output["future_research_directions"],
    )
