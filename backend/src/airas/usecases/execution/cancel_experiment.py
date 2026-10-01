from typing import Any

from airas.core.types.execution_backend import ExecutionBackend
from airas.core.types.github import require_github_repo
from airas.infra.github_client import GithubClient
from airas.infra.seyval_client import SeyvalClient


async def cancel_experiment(
    execution_id: str,
    *,
    backend: ExecutionBackend,
    github_client: GithubClient | None = None,
    seyval_client: SeyvalClient | None = None,
    github_owner: str | None = None,
    repository_name: str | None = None,
) -> dict[str, Any]:
    # cancelled は中止要求が受理されたかどうかで、run が実際に止まったかは
    # get_experiment_run_status で確認する（TODO: 名前を accepted に寄せるか検討）
    match backend:
        case "github_actions":
            if github_client is None:
                raise ValueError('backend="github_actions" needs a github_client')

            github_owner, repository_name = require_github_repo(
                github_owner, repository_name
            )
            cancelled = await github_client.acancel_workflow_run(
                github_owner=github_owner,
                repository_name=repository_name,
                workflow_run_id=int(execution_id),
            )
            return {
                "execution_id": execution_id,
                "backend": backend,
                "cancelled": cancelled,
                "status": None,
            }
        case "seyval":
            if seyval_client is None:
                raise ValueError('backend="seyval" needs a seyval_client')
            await seyval_client.acancel_run(execution_id)
            # cancel のレスポンス形式は保証されていないので、status は run を読み直して取る
            status = (await seyval_client.aget_run(execution_id)).get("status")
            return {
                "execution_id": execution_id,
                "backend": backend,
                "cancelled": status not in ("completed", "failed"),
                "status": status,
            }
        case _:
            raise ValueError(f"unknown backend {backend!r}")
