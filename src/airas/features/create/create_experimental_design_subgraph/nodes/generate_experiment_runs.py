import itertools
import logging
import re

from airas.types.research_iteration import ExperimentRun
from airas.types.research_session import ResearchSession

logger = logging.getLogger(__name__)


def _sanitize_for_branch_name(text: str) -> str:
    # Allow alphanumeric, dots, hyphens, underscores
    sanitized = re.sub(r"[^a-zA-Z0-9._-]+", "-", text)
    # Remove leading/trailing dots and hyphens
    sanitized = sanitized.strip(".-")
    # Replace consecutive dots with single dot (.. is not allowed)
    sanitized = re.sub(r"\.{2,}", ".", sanitized)
    # Remove .lock suffix if present
    if sanitized.endswith(".lock"):
        sanitized = sanitized[:-5]
    return sanitized


def generate_experiment_runs(
    research_session: ResearchSession,
) -> list[ExperimentRun]:
    if not (design := research_session.current_iteration.experimental_design):
        logger.error("No experimental_design found in current_iteration")
        return []

    methods = ["proposed"]
    comparative_ids = [
        f"comparative-{i + 1}" for i in range(len(design.comparative_methods))
    ]
    methods.extend(comparative_ids)

    # Use placeholder if models or datasets are empty (e.g., when proposed method introduces new model/dataset)
    models = design.models_to_use or [None]
    datasets = design.datasets_to_use or [None]

    if design.models_to_use is None or len(design.models_to_use) == 0:
        logger.warning("No models specified (proposed method may introduce new model)")
    if design.datasets_to_use is None or len(design.datasets_to_use) == 0:
        logger.warning(
            "No datasets specified (proposed method may introduce new dataset)"
        )

    return [
        ExperimentRun(
            run_id=_sanitize_for_branch_name(
                "-".join(filter(None, [method, model, dataset]))
            ),
            method_name=method,
            model_name=model,
            dataset_name=dataset,
        )
        for method, model, dataset in itertools.product(methods, models, datasets)
    ]
