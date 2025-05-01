from pydantic import BaseModel
from jinja2 import Environment
from airas.utils.api_client.llm_facade_client import LLMFacadeClient, LLM_MODEL
from airas.retrieve.retrieve_code_subgraph.prompt.extract_experimental_info_prompt import (
    extract_experimental_info_prompt,
)


class LLMOutput(BaseModel):
    extract_code: str
    extract_info: str


def extract_experimental_info(
    model_name: LLM_MODEL, method_text: str, repository_content_str
) -> tuple[str, str]:
    client = LLMFacadeClient(model_name)
    env = Environment()
    template = env.from_string(extract_experimental_info_prompt)
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


if __name__ == "__main__":
    method_text = "This is a test method."
    repository_content_str = "This is a test repository content."
    extract_code, extract_info = extract_experimental_info(
        model_name="gemini-2.0-flash-001",
        method_text=method_text,
        repository_content_str=repository_content_str,
    )
    print("Extracted Code:", extract_code)
    print("Extracted Info:", extract_info)
