from typing_extensions import TypedDict


class CreateCodeLocalSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str
    new_method: str
    experiment_code: str
    experiment_iteration: int
