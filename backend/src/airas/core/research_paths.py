from pathlib import Path

# Where an experiment run writes its results, relative to the repository
# root (and, during a run, to the working directory). Passed to the entry
# point as `results_dir=`.
RESULTS_DIR = ".research/results"

# The paper's canonical record: preregistered declarations plus the
# machine-computed results layer. One per repository, shared by every
# LaTeX template.
RECORD_FILENAME = "record.json"
RECORD_PATH = f".research/{RECORD_FILENAME}"
# The design before the freeze: the `preregister_record` arguments as the agent
# agreed them, which a sanity run is reviewed against.
DESIGN_PATH = ".research/design.json"

# What a run writes into its .research/results/<run_id>/ directory, and the
# reserved directory name for cross-run aggregates.
METRICS_FILENAME = "metrics.json"
COMPARISON_KEY = "comparison"
COMPARISON_METRICS_FILENAME = "aggregated_metrics.json"
OBSERVED_FILENAME = "observed.json"
# A model's reading of the run's code and observation against its declaration,
# written by the run workflow after the run and imported with the run.
IMPLEMENTATION_REVIEW_FILENAME = "implementation_review.json"

# The trusted layer the template ships and the agent may not edit: the
# Makefile every run goes through, and the observation hook it puts on
# PYTHONPATH so every Python process of a run writes what it loaded and called.
MAKEFILE_PATH = "Makefile"
HOOK_PATH = ".airas/sitecustomize.py"
TRUSTED_PATHS = (MAKEFILE_PATH, ".github", ".airas")

# The literature the research drew on: one directory per source holding
# the paper's text and/or its repository's snapshot (one page per file),
# which its quoted passages are checked against. Pages are separated by a
# form feed, as pdftotext does.
SOURCES_DIR = ".research/sources"
FULLTEXT_FILENAME = "fulltext.txt"


def fulltext_relpath(source_id: str) -> str:
    return f"{SOURCES_DIR}/{source_id}/{FULLTEXT_FILENAME}"


def repository_snapshot_relpath(repository_id: str) -> str:
    """'s1.r2' -> '.research/sources/s1/r2.txt'"""
    source_id, suffix = repository_id.split(".")
    return f"{SOURCES_DIR}/{source_id}/{suffix}.txt"


PAGE_SEPARATOR = "\f"
REFERENCES_BIB_FILENAME = "references.bib"

# The fork point: what an agent needs to resume the research from a commit.
# One directory per harness session holding the raw transcript, its neutral
# rendering and the harness configuration; one JSONL of step boundaries.
SESSIONS_DIR = ".research/sessions"
STEPS_PATH = ".research/trace/steps.jsonl"
DERIVED_FROM_PATH = ".research/derived_from.json"

# Method diagrams, by the current convention.
DIAGRAM_DIR = f"{RESULTS_DIR}/diagram"

# Diagrams used to live at the repository root instead. Kept for older
# repositories; remove in the next major release (see issue #913).
LEGACY_DIAGRAM_DIR = ".research/diagrams"


def repo_root(local_path: str) -> Path:
    return Path(local_path).expanduser().resolve()


def record_path(local_path: str) -> Path:
    return repo_root(local_path) / RECORD_PATH
