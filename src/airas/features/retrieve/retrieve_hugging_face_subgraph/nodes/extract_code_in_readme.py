import json

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_hugging_face_subgraph.prompt.extract_code_in_readme_prompt import (
    extract_code_in_readme_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github


class LLMOutput(BaseModel):
    extracted_code: str


def extract_code_in_readme(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    github_repository_info: GitHubRepositoryInfo,
    client: LLMFacadeClient | None = None,
) -> ResearchHypothesis:
    client = client or LLMFacadeClient(llm_name=llm_name)
    env = Environment()
    template = env.from_string(extract_code_in_readme_prompt)
    for index, huggingface_data in enumerate(
        new_method.experimental_design.external_resources.hugging_face.models
    ):
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
        save_io_on_github(
            github_repository_info=github_repository_info,
            input=messages,
            output=json.dumps(output, ensure_ascii=False, indent=4),
            subgraph_name="retrieve_hugging_face_subgraph",
            node_name=f"extract_code_in_readme_model_{index}",
        )
        huggingface_data.extracted_code = output["extracted_code"]
    for index, dataset in enumerate(
        new_method.experimental_design.external_resources.hugging_face.datasets
    ):
        if dataset.readme == "":
            dataset.extracted_code = ""
            continue
        messages = template.render(
            {
                "huggingface_readme": dataset.readme,
            }
        )
        output, _cost = client.structured_outputs(
            message=messages, data_model=LLMOutput
        )
        if output is None:
            dataset.extracted_code = ""
            continue
        save_io_on_github(
            github_repository_info=github_repository_info,
            input=messages,
            output=json.dumps(output, ensure_ascii=False, indent=4),
            subgraph_name="retrieve_hugging_face_subgraph",
            node_name=f"extract_code_in_readme_dataset_{index}",
        )
        dataset.extracted_code = output["extracted_code"]

    return new_method
