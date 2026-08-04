import asyncio
import logging
import posixpath

from airas.core.research_paths import RESULTS_DIR
from airas.infra.aixs_client import AixsClient

logger = logging.getLogger(__name__)

# Presigned download URLs expire, so fetch the batch promptly; a few at a
# time is enough to keep that window short without hammering S3.
MAX_CONCURRENT_DOWNLOADS = 5
# A circuit breaker, not a capacity limit: what belongs here is one run's
# metrics and figures. A rendered vector figure is tens of KB, a pathological
# one (thousands of marks) a couple of MB, and a paper carries well under
# twenty — so a real import is a few MB and an extreme one still under ~40.
# Past that, the run is writing checkpoints or datasets into the results
# directory, and those must not enter git history, which is permanent.
# 50 MB is also where GitHub itself starts warning about a single file.
MAX_TOTAL_BYTES = 50 * 1024 * 1024
# Largest offenders named in the error, so the cause is actionable.
_OVERSIZE_REPORT_COUNT = 5


def _is_importable(path: str) -> bool:
    """Whether an output path may be written into the repository.

    Output paths are produced by the experiment code, which is untrusted:
    only plain relative paths that stay inside the results directory are
    accepted, so a run cannot write over anything else in the repository.
    """
    if not path or path.startswith("/") or "\\" in path:
        return False
    if not path.startswith(f"{RESULTS_DIR}/"):
        return False
    # normpath collapses any "..", so a path that escapes changes shape.
    return posixpath.normpath(path) == path


async def collect_run_outputs(
    aixs_client: AixsClient,
    execution_id: str,
) -> dict[str, bytes]:
    """Download a run's result files, keyed by their repository path.

    The bytes stay inside this process: the presigned URLs AIXS hands out
    are unauthenticated, time-limited capabilities, and the files themselves
    are whatever the experiment code wrote.
    """
    listing = await aixs_client.aget_run_outputs(execution_id)

    if listing.get("truncated"):
        raise ValueError(
            f"AIXS truncated the output listing for run {execution_id}, so an "
            "import would silently drop files. Reduce what the run writes "
            "outside the results directory, or import the files manually."
        )

    outputs = listing.get("outputs") or []
    results = [item for item in outputs if _is_importable(item.get("path", ""))]
    skipped = len(outputs) - len(results)
    if skipped:
        logger.info(
            f"Skipping {skipped} of {len(outputs)} output files outside {RESULTS_DIR}/"
        )

    if not results:
        raise ValueError(
            f"AIXS run {execution_id} produced no files under {RESULTS_DIR}/ "
            f"({len(outputs)} output files in total). Check that the run "
            "succeeded and wrote its results where the CLI contract expects."
        )

    total_bytes = sum(int(item.get("size_bytes") or 0) for item in results)
    if total_bytes > MAX_TOTAL_BYTES:
        largest = sorted(
            results, key=lambda item: int(item.get("size_bytes") or 0), reverse=True
        )[:_OVERSIZE_REPORT_COUNT]
        offenders = ", ".join(
            f"{item['path']} ({item.get('size_bytes')} bytes)" for item in largest
        )
        raise ValueError(
            f"AIXS run {execution_id} wrote {total_bytes} bytes under "
            f"{RESULTS_DIR}/, over the {MAX_TOTAL_BYTES}-byte import limit. "
            f"Largest files: {offenders}. Results are committed to git, whose "
            "history is permanent, so keep checkpoints and datasets out of "
            f"{RESULTS_DIR}/."
        )

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

    async def download(item: dict) -> tuple[str, bytes]:
        # The path is guaranteed by the filter above; the URL is not, and a
        # bare KeyError from inside the gather would not say which file.
        path = item["path"]
        url = item.get("download_url")
        if not url:
            raise ValueError(
                f"AIXS listed {path} for run {execution_id} without a "
                "download_url, so it cannot be imported."
            )
        async with semaphore:
            return path, await aixs_client.adownload(url)

    logger.info(
        f"Downloading {len(results)} output files ({total_bytes} bytes) "
        f"from AIXS run {execution_id}"
    )
    downloaded = await asyncio.gather(*(download(item) for item in results))
    return dict(downloaded)
