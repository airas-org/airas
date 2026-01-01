import itertools
import logging
import re

from airas.types.research_iteration import ExperimentRun
from airas.types.research_session import ResearchSession

logger = logging.getLogger(__name__)


def _sanitize_for_branch_name(text: str) -> str:
    sanitized = re.sub(
        r"[^a-zA-Z0-9._-]+", "-", text
    )  # Allow alphanumeric, dots, hyphens, underscores
    sanitized = sanitized.strip(".-")  # Remove leading/trailing dots and hyphens
    sanitized = re.sub(
        r"\.{2,}", ".", sanitized
    )  # Replace consecutive dots with single dot (.. is not allowed)
    sanitized = re.sub(
        r"-{2,}", "-", sanitized
    )  # Replace consecutive hyphens with single hyphen
    if sanitized.endswith(".lock"):  # Remove .lock suffix if present
        sanitized = sanitized[:-5]
    return sanitized


def generate_experiment_runs(
    research_session: ResearchSession,
) -> list[ExperimentRun]:
    if not (design := research_session.current_iteration.experimental_design):
        logger.error("No experimental_design found in current_iteration")
        return []

    iteration_id = research_session.current_iteration.iteration_id

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
                "-".join(filter(None, [method, f"iter{iteration_id}", model, dataset]))
            ),
            method_name=method,
            model_name=model,
            dataset_name=dataset,
        )
        for method, model, dataset in itertools.product(methods, models, datasets)
    ]
