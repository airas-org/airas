from logging import getLogger

from airas.utils.api_client.github_client import GithubClient, GithubClientError

logger = getLogger(__name__)


def is_repository_created_from_template(
    github_owner: str, 
    repository_name: str,
    template_owner: str, 
    template_repo: str,  
    client: GithubClient | None = None, 
    ) -> bool:
    if client is None:
        client = GithubClient()

    try:
        response = client.get_repository(
            github_owner=github_owner,
            repository_name=repository_name,
        )
    except GithubClientError as e:
        logger.warning(f"Failed to fetch repository metadata: {e}")
        return False
    
    template_info = response.get("template_repository")
    if not template_info:
        return False
    
    return (
        template_info.get("owner", {}).get("login") == template_owner and
        template_info.get("name") == template_repo
    )