import hashlib
import time
from pathlib import Path

from airas.core.research_paths import PAGE_SEPARATOR

CACHE_DIR = Path("~/.airas/cache/fulltext").expanduser()
_TTL_SECONDS = 7 * 24 * 3600


def cache_path(pdf_url: str, cache_dir: Path = CACHE_DIR) -> Path:
    return cache_dir / f"{hashlib.sha256(pdf_url.encode()).hexdigest()}.txt"


def cache_fulltext(pdf_url: str, pages: list[str], cache_dir: Path = CACHE_DIR) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - _TTL_SECONDS
    for stale in cache_dir.glob("*.txt"):
        if stale.stat().st_mtime < cutoff:
            stale.unlink(missing_ok=True)

    path = cache_path(pdf_url, cache_dir)
    # Same layout as .research/sources/<id>/fulltext.txt, so registering is a copy.
    path.write_text(PAGE_SEPARATOR.join(pages), encoding="utf-8")
    return path


def cached_fulltext(pdf_url: str, cache_dir: Path = CACHE_DIR) -> list[str] | None:
    path = cache_path(pdf_url, cache_dir)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").split(PAGE_SEPARATOR)
