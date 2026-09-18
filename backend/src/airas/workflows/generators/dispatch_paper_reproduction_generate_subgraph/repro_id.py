import re
from datetime import datetime, timezone
from urllib.parse import urlparse

_ARXIV_ID_PATTERN = re.compile(r"arxiv\.org/\S*?(\d{4}\.\d{4,5})")

# repro_id is interpolated into a GitHub Actions workflow_dispatch input (e.g.
# `.reproduction/${{ inputs.repro_id }}`) and, on the fetch side, a GitHub Contents API path
# segment. Restrict it to generate_repro_id's own output charset and reject "."/".." outright so a
# crafted value can't escape the .reproduction/<repro_id>/ directory.
_REPRO_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_repro_id(value: str) -> str:
    if value in (".", "..") or not _REPRO_ID_RE.fullmatch(value):
        raise ValueError(f"invalid repro_id: {value!r}")
    return value


def _extract_paper_id(paper_url: str) -> str | None:
    match = _ARXIV_ID_PATTERN.search(paper_url)
    if match is not None:
        return match.group(1)
    path = urlparse(paper_url).path.strip("/")
    if not path:
        return None
    return path.rsplit("/", 1)[-1]


def generate_repro_id(paper_url: str) -> str:
    """Build a reproduction ID: '<paper ID>-<YYYYMMDD-HHMMSS UTC>' (or just the
    timestamp '<YYYYMMDD-HHMMSS UTC>' when no paper ID can be extracted). The
    paper ID is the arXiv ID if found, otherwise the last path segment of the
    URL. Characters are normalized to [A-Za-z0-9._-] so the ID is safe as a
    directory name in the experiment repository."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    paper_id = _extract_paper_id(paper_url)
    if paper_id is None:
        return timestamp
    paper_id = re.sub(r"[^A-Za-z0-9._-]", "-", paper_id)
    return f"{paper_id}-{timestamp}"
