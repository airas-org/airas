from airas.data.datasets.language_model_fine_tuning_dataset import (
    LANGUAGE_MODEL_FINE_TUNING_DATASET_LIST,
)
from airas.types.experimental_design import DatasetSubfield


def retrieve_datasets(dataset_subfield: DatasetSubfield) -> dict:
    if dataset_subfield == "language_model_fine_tuning_dataset":
        return LANGUAGE_MODEL_FINE_TUNING_DATASET_LIST
