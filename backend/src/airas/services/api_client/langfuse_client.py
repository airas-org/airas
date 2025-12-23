import logging
import os

from langfuse.langchain import CallbackHandler

from airas.services.api_client.retry_policy import make_retry_policy

logger = logging.getLogger(__name__)

LANGFUSE_RETRY = make_retry_policy()


class LangfuseClient:
    def __init__(self) -> None:
        self._enabled = self._check_enabled()

    def _check_enabled(self) -> bool:
        required_vars = ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY"]

        if missing := [var for var in required_vars if not os.getenv(var)]:
            logger.info(
                f"LangFuse tracing disabled. Missing environment variables: {', '.join(missing)}"
            )
            return False

        return True

    @LANGFUSE_RETRY
    def create_handler(self) -> CallbackHandler | None:
        if not self._enabled:
            logger.debug("LangFuse is disabled, returning None handler")
            return None

        try:
            logger.info("LangFuse tracing enabled, creating CallbackHandler")
            return CallbackHandler()
        except Exception:
            logger.exception(
                "Failed to initialize LangFuse CallbackHandler; "
                "disabling tracing for this request."
            )
            return None
