"""Check that every URL in the library docs registry is still reachable.

Run from the repository root:
    PYTHONPATH=backend/src python3 backend/scripts/check_library_docs_urls.py

Exits non-zero if any URL fails, listing the broken entries so the registry
can be updated. Uses only the standard library so it runs without installing
the package.
"""

import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from airas.resources.libraries.library_docs import LIBRARY_DOCS

HEADERS = {"User-Agent": "airas-library-docs-linkcheck/1.0"}


def check_url(url: str) -> str | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status >= 400:
                return f"HTTP {resp.status}"
            if url.endswith(("llms.txt", "llms-full.txt")):
                head = resp.read(300).decode("utf-8", errors="replace").lower()
                if "<html" in head or head.startswith("<!"):
                    return "returned HTML instead of plain text"
        return None
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:
        return str(e)


def check_entry(item: tuple[str, dict]) -> list[str]:
    name, entry = item
    failures = []
    for field in ("official_docs", "github", "llms_txt", "llms_full_txt"):
        url = entry.get(field)
        if not url:
            continue
        error = check_url(url)
        if error:
            failures.append(f"{name}.{field}: {url} -> {error}")
    return failures


def main() -> int:
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = pool.map(check_entry, LIBRARY_DOCS.items())
    failures = [line for lines in results for line in lines]
    total_urls = sum(
        1
        for e in LIBRARY_DOCS.values()
        for f in ("official_docs", "github", "llms_txt", "llms_full_txt")
        if e.get(f)
    )
    print(f"Checked {total_urls} URLs across {len(LIBRARY_DOCS)} libraries.")
    if failures:
        print(f"\n{len(failures)} broken URL(s):")
        for line in failures:
            print(f"  {line}")
        return 1
    print("All URLs reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
