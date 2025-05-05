import glob
import os
import shutil
import zipfile
from logging import getLogger

from airas.utils.api_request_handler import fetch_api_data, retry_request

logger = getLogger(__name__)


def _request_github_actions_artifacts(
    headers: dict, github_owner: str, repository_name: str
):
    url = f"https://api.github.com/repos/{github_owner}/{repository_name}/actions/artifacts"
    return retry_request(fetch_api_data, url, headers=headers, method="GET")


def _parse_artifacts_info(artifacts_infos: dict, workflow_run_id: str):
    artifacts_redirect_url_dict = {}
    for artifacts_info in artifacts_infos["artifacts"]:
        if artifacts_info["workflow_run"]["id"] == workflow_run_id:
            artifacts_redirect_url_dict[artifacts_info["name"]] = artifacts_info[
                "archive_download_url"
            ]
    return artifacts_redirect_url_dict


def _request_download_artifacts(
    headers: dict, artifacts_redirect_url_dict: dict, iteration_save_dir: str
):
    for key, url in artifacts_redirect_url_dict.items():
        response = retry_request(
            fetch_api_data, url, headers=headers, method="GET", stream=True
        )
        _zip_to_txt(response, iteration_save_dir, key)


def _zip_to_txt(response, iteration_save_dir, key):
    zip_file_path = os.path.join(iteration_save_dir, f"{key}.zip")
    with open(zip_file_path, "wb") as f:
        f.write(response)
    logger.info(f"Downloaded artifact saved to: {zip_file_path}")
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(iteration_save_dir)
    logger.info(f"Extracted artifact to: {iteration_save_dir}")
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)
        logger.info(f"ZIP file deleted: {zip_file_path}")


def _copy_images_to_latest_dir(source_dir: str, dest_dir: str):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
        logger.info(f"Removed exisiting images/ directory: {dest_dir}")
    os.makedirs(dest_dir, exist_ok=True)

    for file_path in glob.glob(os.path.join(source_dir, "*.pdf")):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(dest_dir, filename)
        shutil.copyfile(file_path, dest_path)
        logger.info(f"Copied image to: {dest_path}")


def retrieve_github_actions_artifacts(
    github_owner,
    repository_name,
    workflow_run_id,
    save_dir,
    fix_iteration_count,
) -> tuple[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    iteration_save_dir = save_dir + f"/iteration_{fix_iteration_count}"
    os.makedirs(iteration_save_dir, exist_ok=True)
    response_artifacts_infos = _request_github_actions_artifacts(
        headers, github_owner, repository_name
    )
    if response_artifacts_infos:
        logger.info("Successfully retrieved artifacts information.")
    else:
        logger.error("Failure to retrieve artifacts information.")
        raise RuntimeError("Failure to retrieve artifacts information.")
    get_artifacts_redirect_url_dict = _parse_artifacts_info(
        response_artifacts_infos, workflow_run_id
    )
    _request_download_artifacts(
        headers, get_artifacts_redirect_url_dict, iteration_save_dir
    )
    with open(os.path.join(iteration_save_dir, "output.txt"), "r") as f:
        output_text_data = f.read()
    with open(os.path.join(iteration_save_dir, "error.txt"), "r") as f:
        error_text_data = f.read()

    _copy_images_to_latest_dir(iteration_save_dir, os.path.join(save_dir, "images"))

    return (
        output_text_data,
        error_text_data,
    )


# if __name__ == "__main__":
#     graph_builder = StateGraph(State)
#     graph_builder.add_node(
#         "retrieve_github_actions_artifacts",
#         RetrieveGithubActionsArtifactsNode(
#             input_key=[
#                 "github_owner",
#                 "repository_name",
#                 "workflow_run_id",
#                 "save_dir",
#                 "num_iterations",
#             ],
#             output_key=["output_file_path", "error_file_path"],
#         ),
#     )
#     graph_builder.add_edge(START, "retrieve_github_actions_artifacts")
#     graph_builder.add_edge("retrieve_github_actions_artifacts", END)
#     graph = graph_builder.compile()
#     state = {
#         "github_owner": "auto-res",
#         "repository_name": "experimental-script",
#         "workflow_run_id": 13055964079,
#         "save_dir": "/workspaces/researchgraph/data",
#         "num_iterations": 1,
#     }
#     graph.invoke(state, debug=True)
