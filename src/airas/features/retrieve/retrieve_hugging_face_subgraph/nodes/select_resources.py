import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_hugging_face_subgraph.prompt.select_resources_prompt import (
    select_resources_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.hugging_face import HuggingFace
from airas.types.research_hypothesis import ExternalResources, ResearchHypothesis

logger = logging.getLogger(__name__)


class LLMOutput(BaseModel):
    selected_models: list[str]
    selected_datasets: list[str]


def select_resources(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    huggingface_search_results: HuggingFace,
    prompt_template: str = select_resources_prompt,
    client: LLMFacadeClient | None = None,
    max_models: int = 10,
    max_datasets: int = 10,
) -> ResearchHypothesis:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(
        {
            "new_method": new_method.model_dump(),
            "huggingface_search_results": _format_huggingface_data(
                huggingface_search_results
            ),
            "max_models": max_models,
            "max_datasets": max_datasets,
        }
    )

    output, _cost = client.structured_outputs(message=messages, data_model=LLMOutput)
    if output is None:
        raise ValueError("Error: No response from LLM in select_resources.")

    selected_models = [
        model
        for model in huggingface_search_results.models
        if model.id in output["selected_models"]
    ]
    selected_datasets = [
        dataset
        for dataset in huggingface_search_results.datasets
        if dataset.id in output["selected_datasets"]
    ]

    logger.info(
        f"Selected {len(selected_models)} models and {len(selected_datasets)} datasets"
    )

    # Create ExternalResources with structured typing
    new_method.experimental_design.external_resources = ExternalResources(
        hugging_face=HuggingFace(models=selected_models, datasets=selected_datasets)
    )

    return new_method


def _format_huggingface_data(huggingface_search_results: HuggingFace) -> str:
    hugging_face_data = huggingface_search_results.model_dump()
    hugging_face_data_str = ""
    hugging_face_data_str += "## Models"
    for model in hugging_face_data["models"]:
        hugging_face_data_str += f"""
- Model Name: {model["id"]}
- README:
  {model["readme"][:3000]}\n"""
    hugging_face_data_str += "\n## Datasets"
    for dataset in hugging_face_data["datasets"]:
        hugging_face_data_str += f"""
- Dataset Name: {dataset["id"]}
- README:
  {dataset["readme"][:3000]}\n"""
    return hugging_face_data_str
