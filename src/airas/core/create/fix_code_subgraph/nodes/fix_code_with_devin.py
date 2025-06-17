from logging import getLogger
from airas.services.api_client.devin_client import DevinClient

logger = getLogger(__name__)

def _request_revision_to_devin(
    session_id: str, output_text_data: str, error_text_data: str
):
    message = f"""
# Instruction
The following error occurred when executing the code in main.py. Please modify the code and push the modified code to the remote repository.
Also, if there is no or little content in “Standard Output”, please modify main.py to make the standard output content richer.
- "Error” contains errors that occur when main.py is run.
- "Standard Output” contains the standard output of the main.py run.
# Error
{error_text_data}
# Standard Output
{output_text_data}"""

    client = DevinClient()
    return client.send_message(
        session_id=session_id,
        message=message,
    )

def fix_code_with_devin(
    session_id: str,
    output_text_data: str,
    error_text_data: str,
):
    response = _request_revision_to_devin(session_id, output_text_data, error_text_data)
    if response is not None:
        raise RuntimeError(
            "Failed to request revision to Devin"
        )
