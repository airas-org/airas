from logging import getLogger

from airas.utils.api_client.github_client import GithubClient

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

    response = client.get_repository(
        github_owner=github_owner,
        repository_name=repository_name,
    )
    if response is None:
        return False
    
    template_info = response.get("template_repository")
    if not template_info:
        return False
    
    return (
        template_info.get("owner", {}).get("login") == template_owner and
        template_info.get("name") == template_repo
    )


if __name__ == "__main__":
    github_owner = "auto-res2"
    repository_name = "experiment_script_matsuzawa"
    template_owner = "airas-org"
    template_repo = "airas-template"

    result = is_repository_created_from_template(
        github_owner, 
        repository_name, 
        template_owner, 
        template_repo
    )
    print(f"result: {result}")