import itertools
import logging

from airas.types.research_hypothesis import ExperimentRun, ResearchHypothesis

logger = logging.getLogger(__name__)


def generate_experiment_runs(
    new_method: ResearchHypothesis,
) -> ResearchHypothesis:
    if not new_method.experimental_design:
        logger.error("No experimental_design found in new_method")
        return new_method

    design = new_method.experimental_design

    methods = ["proposed"]
    comparative_ids = [
        f"comparative-{i + 1}" for i in range(len(design.comparative_methods))
    ]
    methods.extend(comparative_ids)

    models = design.models_to_use or []
    datasets = design.datasets_to_use or []

    if not models:
        logger.warning("No models specified in experimental design")
    if not datasets:
        logger.warning("No datasets specified in experimental design")

    experiment_runs = [
        ExperimentRun(
            run_id=f"{method}-{model}-{dataset}",
            method_name=method,
            model_name=model,
            dataset_name=dataset,
        )
        for method, model, dataset in itertools.product(methods, models, datasets)
    ]

    new_method.experiment_runs = experiment_runs
    logger.info(
        f"Generated {len(experiment_runs)} experiment runs: "
        f"{len(methods)} methods × {len(models)} models × {len(datasets)} datasets"
    )

    return new_method
