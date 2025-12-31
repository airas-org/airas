from airas.data.datasets.image_dataset import IMAGES_DATASETS
from airas.data.datasets.language_model_fine_tuning_dataset import (
    LANGUAGE_MODEL_FINE_TUNING_DATASETS,
)
from airas.types.experimental_design import DatasetSubfield


def retrieve_datasets(dataset_subfield: DatasetSubfield):
    if dataset_subfield == "language_model_fine_tuning_datasets":
        return LANGUAGE_MODEL_FINE_TUNING_DATASETS
    elif dataset_subfield == "image_datasets":
        return IMAGES_DATASETS
