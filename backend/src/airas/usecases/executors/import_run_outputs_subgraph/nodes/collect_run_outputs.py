import asyncio
import logging
import posixpath

from airas.core.research_paths import RESULTS_DIR
from airas.core.types.run_provenance import PROVENANCE_MANIFEST_PATH
from airas.infra.run_output_store import MAX_TOTAL_BYTES, RunOutputStore

logger = logging.getLogger(__name__)

MAX_CONCURRENT_DOWNLOADS = 5
_OVERSIZE_REPORT_COUNT = 5


def _is_importable(path: str) -> bool:
    """Output paths come from untrusted experiment code: only plain relative
    paths inside the results directory, and never the manifest the import
    itself writes."""
    if not path or path.startswith("/") or "\\" in path:
        return False
    if not path.startswith(f"{RESULTS_DIR}/") or path == PROVENANCE_MANIFEST_PATH:
        return False
    return posixpath.normpath(path) == path


async def collect_run_outputs(
    store: RunOutputStore,
    execution_id: str,
) -> dict[str, bytes]:
    """Download a run's result files, keyed by their repository path. The bytes
    stay inside this process."""
    listed = await store.alist_outputs(execution_id)
    results = {path: size for path, size in listed.items() if _is_importable(path)}
    skipped = len(listed) - len(results)
    if skipped:
        logger.info(
            f"Skipping {skipped} of {len(listed)} output files outside {RESULTS_DIR}/"
        )

    if not results:
        raise ValueError(
            f"{store.backend} run {execution_id} produced no files under "
            f"{RESULTS_DIR}/ ({len(listed)} output files in total). Check that "
            "the run succeeded and wrote its results where the CLI contract expects."
        )

    total_bytes = sum(results.values())
    if total_bytes > MAX_TOTAL_BYTES:
        largest = sorted(results.items(), key=lambda item: item[1], reverse=True)
        offenders = ", ".join(
            f"{path} ({size} bytes)" for path, size in largest[:_OVERSIZE_REPORT_COUNT]
        )
        raise ValueError(
            f"{store.backend} run {execution_id} wrote {total_bytes} bytes under "
            f"{RESULTS_DIR}/, over the {MAX_TOTAL_BYTES}-byte import limit. "
            f"Largest files: {offenders}. Results are committed to git, whose "
            "history is permanent, so keep checkpoints and datasets out of "
            f"{RESULTS_DIR}/."
        )

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    async def download(path: str) -> tuple[str, bytes]:
        async with semaphore:
            return path, await store.adownload(execution_id, path)

    logger.info(
        f"Downloading {len(results)} output files ({total_bytes} bytes) "
        f"from {store.backend} run {execution_id}"
    )
    downloaded = await asyncio.gather(*(download(path) for path in results))
    return dict(downloaded)
