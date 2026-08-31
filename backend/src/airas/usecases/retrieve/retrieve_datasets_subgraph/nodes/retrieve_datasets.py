from airas.core.types.experimental_design import DatasetSubfield
from airas.resources.datasets.registry import DATASETS_BY_SUBFIELD


def retrieve_datasets(dataset_subfield: DatasetSubfield):
    return DATASETS_BY_SUBFIELD.get(dataset_subfield, {})
