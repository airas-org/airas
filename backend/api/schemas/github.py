from typing_extensions import TypedDict

from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession


class PrepareRepositoryRequestBody(TypedDict):
    github_repository_info: GitHubRepositoryInfo


class PrepareRepositoryResponseBody(TypedDict):
    pass


class PushCodeRequestBody(TypedDict):
    research_session: ResearchSession
    github_repository_info: GitHubRepositoryInfo


class PushCodeResponseBody(TypedDict):
    pass
