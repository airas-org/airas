from typing import Optional

from pydantic import BaseModel, Field


class GitHubRepositoryInfo(BaseModel):
    github_owner: str = Field(..., description="GitHub owner of the repository")
    repository_name: str = Field(..., description="Name of the repository")
    branch_name: str = Field(..., description="Branch name")
    child_branches: Optional[list[str]] = Field(
        None, description="Child branches created for experiments"
    )

    def add_child_branch(self, experiment_id: str, variation_id: str) -> str:
        child_branch_name = f"{self.branch_name}-{experiment_id}-{variation_id}"
        if self.child_branches is None:
            self.child_branches = []
        self.child_branches.append(child_branch_name)
        return child_branch_name
