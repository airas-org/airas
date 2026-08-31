"""Paths the experiment repository is expected to use.

These are a contract, not a preference: the experiment code writes results
where airas-template's CLI contract says to, and the LaTeX build and the
Overleaf export collect figures from the same places. Changing a value here
without changing the template breaks that handshake, so keep them defined
once.
"""

# Where an experiment run writes its results, relative to the repository
# root (and, during a run, to the working directory). Passed to the entry
# point as `results_dir=`.
RESULTS_DIR = ".research/results"

# Method diagrams, by the current convention.
DIAGRAM_DIR = f"{RESULTS_DIR}/diagram"

# Diagrams used to live at the repository root instead. Kept for older
# repositories; remove in the next major release (see issue #913).
LEGACY_DIAGRAM_DIR = ".research/diagrams"
