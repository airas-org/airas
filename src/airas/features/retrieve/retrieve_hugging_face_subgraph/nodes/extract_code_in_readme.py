from dependency_injector import providers
from dependency_injector.wiring import Provide, inject
from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_hugging_face_subgraph.prompt.extract_code_in_readme_prompt import (
    extract_code_in_readme_prompt,
)
from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_session import ResearchSession


class LLMOutput(BaseModel):
    extracted_code: str


@inject
def extract_code_in_readme(
    llm_name: LLM_MODEL,
    research_session: ResearchSession,
    llm_facade_provider: providers.Factory[LLMFacadeClient] = Provide[
        SyncContainer.llm_facade_provider
    ],
) -> ResearchSession:
    if not research_session.current_iteration:
        return research_session

    experimental_design = research_session.current_iteration.experimental_design
    if (
        not experimental_design
        or not experimental_design.external_resources
        or not experimental_design.external_resources.hugging_face
    ):
        return research_session

    client = llm_facade_provider(llm_name=llm_name)
    env = Environment()
    template = env.from_string(extract_code_in_readme_prompt)
    for huggingface_data in experimental_design.external_resources.hugging_face.models:
        if huggingface_data.readme == "":
            huggingface_data.extracted_code = ""
            continue
        messages = template.render(
            {
                "huggingface_readme": huggingface_data.readme,
            }
        )
        output, _cost = client.structured_outputs(
            message=messages, data_model=LLMOutput
        )
        if output is None:
            huggingface_data.extracted_code = ""
            continue

        huggingface_data.extracted_code = output["extracted_code"]

    return research_session
