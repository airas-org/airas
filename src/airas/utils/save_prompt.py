from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo


def save_io_on_github(
    github_repository_info: GitHubRepositoryInfo,
    input: str,
    output: str,
    subgraph_name: str,
    node_name: str,
    client: GithubClient | None = None,
) -> None:
    if client is None:
        client = GithubClient()
    file_path = f".research/prompt/{subgraph_name}/{node_name}.txt"
    text = f"""
Input:
{input}
Output:
{output}
"""
    text_bytes = text.encode("utf-8")
    client.commit_file_bytes(
        github_owner=github_repository_info.github_owner,
        repository_name=github_repository_info.repository_name,
        branch_name=github_repository_info.branch_name,
        file_path=file_path,
        file_content=text_bytes,
        commit_message="Research paper uploaded.",
    )
    return
