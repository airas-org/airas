import time

from airas.services.api_client.devin_client import DevinClient


def check_devin_completion(session_id: str) -> bool:
    client = DevinClient()
    while True:
        response = client.retrieve_session(session_id)
        status = response.get("status_enum")
        # NOTE:You can check the session status from the following options.
        # https://docs.devin.ai/api-reference/sessions/retrieve-details-about-an-existing-session#response-status-enum
        if status in ["blocked", "finished"]:
            return True

        time.sleep(30)
