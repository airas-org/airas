import re

# repro_id is interpolated into a GitHub Actions workflow_dispatch input (e.g.
# `.reproduction/${{ inputs.repro_id }}`) and, on the fetch side, a GitHub Contents API path
# segment. Restrict it to generate_repro_id's own output charset and reject "."/".." outright so a
# crafted value can't escape the .reproduction/<repro_id>/ directory.
_REPRO_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_repro_id(value: str) -> str:
    if value in (".", "..") or not _REPRO_ID_RE.fullmatch(value):
        raise ValueError(f"invalid repro_id: {value!r}")
    return value
