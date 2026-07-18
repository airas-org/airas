import base64
import json
import logging
import os

from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient, GithubClientFatalError

logger = logging.getLogger(__name__)

_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")


async def fetch_repository_files(
    github_client: GithubClient,
    github_config: GitHubConfig,
    dir_path: str,
    file_names: tuple[str, ...],
    *,
    ignore_missing: bool = True,
) -> dict:
    """Fetch and decode named files from a directory on the GitHub branch.

    Args:
        dir_path: Directory path in the repository (e.g. ``.reproduction/results``).
        file_names: File names to fetch from that directory.
        ignore_missing: If True (default), skip files that are absent or fail to
            fetch/decode. If False, raise ``GithubClientFatalError`` for those cases.

    Returns:
        A dict keyed by a normalized file name:

        - ``result.json`` → ``{"result": <parsed JSON>}``
        - ``repro.md`` → ``{"repro_md": "<text>"}``
        - ``repro.png`` → ``{"repro_png_base64": "<base64>"}``

        Rules: ``.json`` is parsed; ``.png``/``.jpg``/``.jpeg`` become base64
        (key ends with ``_base64``); other extensions become UTF-8 text
        (``.`` in the name becomes ``_``).

    Raises:
        GithubClientFatalError: If ``dir_path`` is missing or not a directory,
            or (when ``ignore_missing`` is False) a requested file is missing
            or cannot be fetched/decoded.
    """
    listing = await github_client.aget_repository_content(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        file_path=dir_path,
        branch_name=github_config.branch_name,
    )
    if not isinstance(listing, list):
        raise GithubClientFatalError(
            f"'{dir_path}' is not a directory: {type(listing).__name__}"
        )

    existing = {f["name"] for f in listing if f.get("type") == "file"}

    result: dict = {}
    for name in file_names:
        if name not in existing:
            if ignore_missing:
                continue
            raise GithubClientFatalError(f"Missing file: {dir_path}/{name}")
        try:
            raw = await github_client.aget_repository_content(
                github_owner=github_config.github_owner,
                repository_name=github_config.repository_name,
                file_path=f"{dir_path}/{name}",
                branch_name=github_config.branch_name,
                as_="bytes",
            )
        except GithubClientFatalError as exc:
            if ignore_missing:
                logger.warning(f"Failed to fetch {dir_path}/{name}: {exc}")
                continue
            raise
        if not isinstance(raw, bytes):
            msg = f"Unexpected content type for {dir_path}/{name}: {type(raw).__name__}"
            if ignore_missing:
                logger.warning(msg)
                continue
            raise GithubClientFatalError(msg)

        suffix = os.path.splitext(name)[1].lower()
        if suffix == ".json":
            try:
                result[name.removesuffix(".json")] = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                if ignore_missing:
                    logger.warning(f"Failed to parse {dir_path}/{name}: {exc}")
                else:
                    raise GithubClientFatalError(
                        f"Failed to parse {dir_path}/{name}: {exc}"
                    ) from exc
        elif suffix in _IMAGE_SUFFIXES:
            result[name.replace(".", "_") + "_base64"] = base64.b64encode(raw).decode(
                "ascii"
            )
        else:
            result[name.replace(".", "_")] = raw.decode("utf-8", errors="replace")

    return result
