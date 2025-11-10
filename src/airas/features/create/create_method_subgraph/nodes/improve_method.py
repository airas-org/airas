from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_method_subgraph.prompts.improve_method_prompt import (
    improve_method_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_session import ResearchSession


class ImprovedMethod(BaseModel):
    improved_method: str


async def improve_method(
    research_session: ResearchSession, llm_name: LLM_MODEL, llm_client: LLMFacadeClient
) -> str:
    env = Environment()

    template = env.from_string(improve_method_prompt)
    data = {
        "research_session": research_session,
    }
    messages = template.render(data)

    output, cost = await llm_client.structured_outputs(
        message=messages,
        data_model=ImprovedMethod,
        llm_name=llm_name,
    )

    if output is None:
        raise ValueError("No response from LLM in improve_method.")
    return output["improved_method"]
