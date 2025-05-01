from airas.utils.api_request_handler import fetch_api_data, retry_request


def _request_revision_to_devin(
    headers, session_id: str, output_text_data: str, error_text_data: str
):
    url = f"https://api.devin.ai/v1/session/{session_id}/message"
    data = {
        "message": f"""
# Instruction
The following error occurred when executing the code in main.py. Please modify the code and push the modified code to the remote repository.
Also, if there is no or little content in “Standard Output”, please modify main.py to make the standard output content richer.
- "Error” contains errors that occur when main.py is run.
- "Standard Output” contains the standard output of the main.py run.
# Error
{error_text_data}
# Standard Output
{output_text_data}""",
    }

    def should_retry(response):
        # Describe the process so that it is True if you want to retry
        return response is not None

    # TODO:RUNNINGならリクエスを送らないようにする
    return retry_request(
        fetch_api_data,
        url,
        headers=headers,
        data=data,
        method="POST",
        check_condition=should_retry,
    )


def fix_code_with_devin(
    headers: dict,
    session_id: str,
    output_text_data: str,
    error_text_data: str,
    fix_iteration_count: int,
) -> int:
    _request_revision_to_devin(headers, session_id, output_text_data, error_text_data)
    return fix_iteration_count + 1
