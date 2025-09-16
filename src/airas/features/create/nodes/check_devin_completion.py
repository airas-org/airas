import time
from logging import getLogger

from airas.services.api_client.devin_client import DevinClient

logger = getLogger(__name__)


def check_devin_completion(session_id: str) -> bool:
    # NOTE:Because Devin’s status can take time to update, a one-minute wait interval has been configured.
    time.sleep(60)
    client = DevinClient()
    while True:
        response = client.retrieve_session(session_id)
        status = response.get("status_enum")
        # NOTE:You can check the session status from the following options.
        # https://docs.devin.ai/api-reference/sessions/retrieve-details-about-an-existing-session#response-status-enum
        logger.info(f"Devin session status: {status}")
        if status in ["blocked", "finished"]:
            return True

        time.sleep(30)
