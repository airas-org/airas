from pathlib import Path
from typing import Any

from airas.core.research_paths import RESULTS_DIR
from airas.research_record.read.read_run_outputs import (
    load_eval_report,
    load_metrics_data,
    load_provenance_manifest,
)

_FIGURE_SUFFIXES = (".pdf", ".png")


def fetch_experiment_results(local_path: str) -> dict[str, Any]:
    """What the runs left under .research/results/ in the clone: per results
    directory its metrics, its airas-eval report and its figures, plus which
    directories the provenance manifest covers."""
    root = Path(local_path).expanduser().resolve()
    results_dir = root / RESULTS_DIR
    if not results_dir.is_dir():
        raise ValueError(f"No {RESULTS_DIR} directory under {root}")
    try:
        metrics = load_metrics_data(local_path)
    except ValueError:
        metrics = {}
    manifest = load_provenance_manifest(root)
    runs: dict[str, Any] = {}
    for run_dir in sorted(p for p in results_dir.iterdir() if p.is_dir()):
        report = load_eval_report(root, run_dir.name)
        runs[run_dir.name] = {
            "metrics": metrics.get(run_dir.name),
            "evaluation": report.model_dump() if report else None,
            "figures": sorted(
                str(p.relative_to(root))
                for p in run_dir.rglob("*")
                if p.suffix in _FIGURE_SUFFIXES
            ),
            "provenance": (
                manifest.dirs[run_dir.name].model_dump()
                if manifest and run_dir.name in manifest.dirs
                else None
            ),
        }
    return {"results_dir": str(results_dir), "runs": runs}
