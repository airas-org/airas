import logging
from functools import wraps
from typing import Any, Callable

from airas.core.types.research_history import ResearchHistory
from airas.core.utils import to_dict_deep
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph

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


def upload_to_github(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self, state: dict[str, Any]) -> dict[str, Any]:
        result = await func(self, state)

        merged = {**state, **result}
        research_history = ResearchHistory(
            **{
                k: v
                for k, v in merged.items()
                if k in ResearchHistory.model_fields.keys()
            }
        )
        try:
            await (
                GithubUploadSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke(
                    {
                        "github_config": merged["github_config"],
                        "research_history": research_history,
                        "commit_message": "Update research history",
                    }
                )
            )
        except Exception as github_error:
            logger.warning(
                "Failed to upload to GitHub for task %s: %s",
                self.task_id,
                github_error,
            )

        return {**result, "research_history": research_history}

    return wrapper
