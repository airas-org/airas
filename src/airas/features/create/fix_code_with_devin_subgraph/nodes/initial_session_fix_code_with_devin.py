import json
from logging import getLogger

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.fix_code_with_devin_subgraph.prompt.initial_session_fix_code_with_devin_prompt import (
    initial_session_fix_code_with_devin_prompt,
)
from airas.services.api_client.devin_client import DevinClient
from airas.types.devin import DevinInfo
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExternalResources, ResearchHypothesis

logger = getLogger(__name__)


def initial_session_fix_code_with_devin(
    github_repository_info: GitHubRepositoryInfo,
    new_method: ResearchHypothesis,
    experiment_iteration: int,
    runner_type: RunnerType,
    client: DevinClient | None = None,
) -> DevinInfo:
    client = client or DevinClient()
    repository_url = f"https://github.com/{github_repository_info.github_owner}/{github_repository_info.repository_name}"

    method_description = new_method.method
    if new_method.experimental_design:
        if new_method.experimental_design.experiment_details:
            method_description += (
                "\n\nExperimental Details:\n"
                + new_method.experimental_design.experiment_details
            )

    data = {
        "repository_url": repository_url,
        "branch_name": github_repository_info.branch_name,
        "new_method": new_method,
        "experiment_iteration": experiment_iteration,
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "huggingface_data": _retrieve_huggingface_data(
            new_method.experimental_design.external_resources
        ),
    }

    env = Environment()
    template = env.from_string(initial_session_fix_code_with_devin_prompt)
    messages = template.render(data)
    # NOTE:適切にトリミングを行う、現状だと出力が長すぎて他の情報が与えられていない
    messages = _adjust_string_length(messages)

    try:
        response = client.create_session(prompt_template=messages)
    except Exception as e:
        raise RuntimeError("Failed to create Devin session") from e

    logger.info("Successfully created Devin session.")
    experiment_session_id = response["session_id"]
    experiment_devin_url = response["url"]
    print(f"Devin URL: {experiment_devin_url}")
    return DevinInfo(session_id=experiment_session_id, devin_url=experiment_devin_url)


def _adjust_string_length(prompt: str) -> str:
    # NOTE: The official prompt length limit is undocumented. Setting arbitrary limits to be safe.
    MAX_LENGTH = 30000

    if len(prompt) > MAX_LENGTH:
        prompt = prompt[:MAX_LENGTH] + "...\n[Content truncated due to length limit]"
        logger.warning(f"prompt truncated to {MAX_LENGTH} characters")
    return prompt


def _retrieve_huggingface_data(external_resources: ExternalResources) -> str:
    hugging_face_data = external_resources.hugging_face.model_dump()
    hugging_face_data_str = ""
    hugging_face_data_str += "## Model\n"
    model_list = hugging_face_data.get("models", [])
    for model in model_list:
        if model.get("readme", "") == "":
            continue
        hugging_face_model_dict = {
            "Model Name": model["id"],
            "Code": model["extracted_code"],
        }
        hugging_face_data_str += json.dumps(
            hugging_face_model_dict, ensure_ascii=False, indent=4
        )
    hugging_face_data_str += "\n## Dataset\n"
    dataset_data = hugging_face_data.get("datasets", [])
    for dataset in dataset_data:
        if dataset.get("readme", "") == "":
            continue
        hugging_face_dataset_dict = {
            "Dataset Name": dataset["id"],
            "Code": dataset["extracted_code"],
        }
        hugging_face_data_str += json.dumps(
            hugging_face_dataset_dict, ensure_ascii=False, indent=4
        )
    return hugging_face_data_str
