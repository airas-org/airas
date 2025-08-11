from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_code_subgraph.prompt.extract_experimental_info_prompt import (
    extract_experimental_info_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import CandidatePaperInfo


class LLMOutput(BaseModel):
    extract_code: str
    extract_info: str


def extract_experimental_info(
    llm_name: LLM_MODEL,
    method_text: CandidatePaperInfo,
    repository_content_str: str,
    prompt_template: str = extract_experimental_info_prompt,
    client: LLMFacadeClient | None = None,
) -> tuple[str, str]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)
    data = {
        "method_text": method_text,
        "repository_content_str": repository_content_str,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise RuntimeError("Failed to get response from Vertex AI.")
    else:
        extract_code = output["extract_code"]
        extract_info = output["extract_info"]
        return extract_code, extract_info
