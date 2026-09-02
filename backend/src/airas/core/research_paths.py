# Where an experiment run writes its results, relative to the repository
# root (and, during a run, to the working directory). Passed to the entry
# point as `results_dir=`.
RESULTS_DIR = ".research/results"

# The paper's canonical record: preregistered declarations plus the
# machine-computed results layer. One per repository, shared by every
# LaTeX template.
RECORD_FILENAME = "record.json"
RECORD_PATH = f".research/{RECORD_FILENAME}"

# Method diagrams, by the current convention.
DIAGRAM_DIR = f"{RESULTS_DIR}/diagram"

# Diagrams used to live at the repository root instead. Kept for older
# repositories; remove in the next major release (see issue #913).
LEGACY_DIAGRAM_DIR = ".research/diagrams"
