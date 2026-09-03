from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from airas.core.research_paths import RESULTS_DIR

PROVENANCE_MANIFEST_FILENAME = ".provenance.json"
PROVENANCE_MANIFEST_PATH = f"{RESULTS_DIR}/{PROVENANCE_MANIFEST_FILENAME}"


class ResultsDirProvenance(BaseModel):
    """Which execution produced the files in one results directory."""

    execution_id: str = Field(
        description="Seyval run id whose stored outputs this directory holds"
    )
    commit_hash: Optional[str] = Field(
        default=None,
        description="Commit that run executed, as recorded by Seyval",
    )
    overrides: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Parameters the dispatch applied on top of the commit, parsed "
            "from the argv Seyval recorded. The commit fixes the config "
            "files but not the dispatch, so this is the only place a "
            "`mode=pilot` run of a design declared as `mode=full` shows up — "
            "and unlike the run's own output it is Seyval's record, which "
            "the experiment code cannot write"
        ),
    )


class RunProvenanceManifest(BaseModel):
    """Declares, per results directory, the run the paper's data comes from.
    {
        "dirs": {
            "run_1":      {"execution_id": "a1b2c3...", "commit_hash": "9f8e7d..."},
            "run_2":      {"execution_id": "d4e5f6...", "commit_hash": "9f8e7d..."},
            "comparison": {"execution_id": "d4e5f6...", "commit_hash": "9f8e7d..."}
        }
    }
    """

    dirs: dict[str, ResultsDirProvenance] = Field(
        default_factory=dict,
        description="Results directory name -> the run that produced it",
    )
