from logging import getLogger

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.fix_code_with_devin_subgraph.nodes.initial_session_fix_code_with_devin import (
    _adjust_string_length,
    _retrieve_huggingface_data,
)
from airas.features.create.fix_code_with_devin_subgraph.prompt.code_fix_devin_prompt import (
    code_fix_devin_prompt,
)
from airas.services.api_client.devin_client import DevinClient
from airas.types.devin import DevinInfo
from airas.types.research_hypothesis import ResearchHypothesis

logger = getLogger(__name__)


def fix_code_with_devin(
    new_method: ResearchHypothesis,
    experiment_iteration: int,
    runner_type: RunnerType,
    devin_info: DevinInfo,
    error_list: list[str],
    client: DevinClient | None = None,
):
    client = client or DevinClient()

    data = {
        "new_method": new_method,
        "experiment_iteration": experiment_iteration,
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "error_list": error_list,  # Previous errors for analysis
        "huggingface_data": _retrieve_huggingface_data(
            new_method.experimental_design.external_resources
        ),
    }

    env = Environment()
    template = env.from_string(code_fix_devin_prompt)
    prompt = template.render(data)
    prompt = _adjust_string_length(prompt)

    try:
        client.send_message(
            session_id=devin_info.session_id,
            message=prompt,
        )
    except Exception as e:
        raise RuntimeError("Failed to send message to Devin") from e
