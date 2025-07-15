import time

from airas.services.api_client.devin_client import DevinClient


def check_devin_completion(session_id: str) -> dict | None:
    client = DevinClient()
    while True:
        response = client.retrieve_session(session_id)
        status = response.get("status_enum")

        if status in ["blocked", "stopped"]:
            return response

        time.sleep(30)
