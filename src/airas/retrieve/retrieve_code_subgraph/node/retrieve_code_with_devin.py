from jinja2 import Environment
from airas.utils.api_request_handler import fetch_api_data, retry_request
from airas.retrieve.retrieve_code_subgraph.prompt.retrieve_code_with_devin_prompt import (
    retrieve_code_with_devin_prompt,
)
from logging import getLogger

logger = getLogger(__name__)


def _request_create_session(headers, github_url, base_method_text):
    env = Environment()
    template = env.from_string(retrieve_code_with_devin_prompt)
    data = {
        "base_method_text": base_method_text,
        "github_url": github_url,
    }
    prompt = template.render(data)
    url = "https://api.devin.ai/v1/sessions"
    data = {
        "prompt": prompt,
        "idempotent": True,
    }
    return retry_request(fetch_api_data, url, headers=headers, data=data, method="POST")


def retrieve_code_with_devin(
    headers: dict, github_url: str | None, base_method_text: str
) -> tuple[str | None, str | None]:
    if github_url is not None:
        response = _request_create_session(headers, github_url, base_method_text)
        if response:
            logger.info("Successfully created Devin session.")
            retrieve_session_id = response["session_id"]
            retrieve_devin_url = response["url"]
            logger.info(f"Devin URL: {retrieve_devin_url}")
            return retrieve_session_id, retrieve_devin_url
        else:
            logger.info("Failed to create Devin session.")
            return None, None
    else:
        return None, None
