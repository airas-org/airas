import logging
from functools import wraps
from typing import Any, Callable

from airas.core.utils import to_dict_deep

logger = logging.getLogger(__name__)


def save_to_db(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self, state: dict[str, Any]) -> dict[str, Any]:
        try:
            result = await func(self, state)
        except Exception:
            try:
                self.e2e_service.update(
                    id=self.task_id,
                    current_step=state.get("current_step"),
                    result=to_dict_deep(state),
                )
            except Exception as db_error:
                logger.warning(
                    "Failed to save error state to DB for task %s: %s",
                    self.task_id,
                    db_error,
                )
            raise

        merged = {**state, **result}
        try:
            self.e2e_service.update(
                id=self.task_id,
                current_step=merged.get("current_step"),
                result=to_dict_deep(merged),
            )
        except Exception as db_error:
            logger.warning(
                "Failed to save state to DB for task %s: %s",
                self.task_id,
                db_error,
            )

        return result

    return wrapper
