from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from airas.core.research_paths import RESULTS_DIR

PROVENANCE_MANIFEST_FILENAME = ".provenance.json"
PROVENANCE_MANIFEST_PATH = f"{RESULTS_DIR}/{PROVENANCE_MANIFEST_FILENAME}"


class ResultsDirProvenance(BaseModel):
    """Which execution produced the files in one results directory."""

    execution_id: str = Field(
        description="The backend's run id whose stored outputs this directory holds"
    )
    backend: Literal["seyval", "github_actions"] = "seyval"
    commit_hash: Optional[str] = Field(
        default=None,
        description="Commit that run executed, as recorded by the backend",
    )
    overrides: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Parameters the dispatch applied on top of the commit, as the "
            "backend recorded them — the only place a `mode=pilot` run of a "
            "design declared as `mode=full` shows up"
        ),
    )
    parameters: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Every parameter the run resolved, as reported by the backend; "
            "empty when it does not supply it"
        ),
    )
    files: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Repository path -> sha256 of every file imported for this "
            "directory; what the gate checks once the backend has dropped "
            "the run"
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
