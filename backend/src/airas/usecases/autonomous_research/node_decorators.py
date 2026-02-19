from functools import wraps
from typing import Any, Callable

from airas.core.types.research_history import ResearchHistory
from airas.core.utils import to_dict_deep
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph


def save_to_db(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self, state: dict[str, Any]) -> dict[str, Any]:
        result = await func(self, state)
        merged = {**state, **result}
        self.e2e_service.update(
            id=self.task_id,
            current_step=merged.get("current_step"),
            result=to_dict_deep(merged),
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
        return {**result, "research_history": research_history}

    return wrapper
