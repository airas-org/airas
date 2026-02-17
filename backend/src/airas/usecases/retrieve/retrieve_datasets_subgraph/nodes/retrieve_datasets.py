from airas.core.types.experimental_design import DatasetSubfield
from airas.resources.datasets.image_dataset import IMAGES_DATASETS
from airas.resources.datasets.language_model_fine_tuning_dataset import (
    LANGUAGE_MODEL_FINE_TUNING_DATASETS,
)
from airas.resources.datasets.prompt_engineering_datasets import (
    PROMPT_ENGINEERING_DATASETS,
)


def retrieve_datasets(dataset_subfield: DatasetSubfield):
    if dataset_subfield == "language_model_fine_tuning_datasets":
        return LANGUAGE_MODEL_FINE_TUNING_DATASETS
    elif dataset_subfield == "image_datasets":
        return IMAGES_DATASETS
    elif dataset_subfield == "prompt_engineering_datasets":
        return PROMPT_ENGINEERING_DATASETS
