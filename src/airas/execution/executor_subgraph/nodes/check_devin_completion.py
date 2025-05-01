import os
from airas.utils.api_request_handler import fetch_api_data, retry_request


def check_devin_completion(headers: dict, session_id: str) -> dict | None:
    DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
    url = f"https://api.devin.ai/v1/session/{session_id}"

    def should_retry(response):
        # Describe the process so that it is True if you want to retry
        return response.get("status_enum") not in ["blocked", "stopped"]

    return retry_request(
        fetch_api_data,
        url,
        headers=headers,
        method="GET",
        check_condition=should_retry,
    )
