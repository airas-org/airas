from pydantic import BaseModel, Field


class GitHubRepositoryInfo(BaseModel):
    github_owner: str = Field(..., description="GitHub owner of the repository")
    repository_name: str = Field(..., description="Name of the repository")
    branch_name: str = Field(..., description="Branch name")
