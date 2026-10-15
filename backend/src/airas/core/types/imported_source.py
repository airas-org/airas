from pydantic import BaseModel, Field, TypeAdapter


class ImportedSource(BaseModel):
    """Which fetch_literature.yml run a `.research/sources/<id>/` came from."""

    workflow_run_id: str
    entry: str = Field(description="The entry's directory in the run's artifact")


# .research/sources/.provenance.json: source id -> where it was imported from
SOURCES_PROVENANCE = TypeAdapter(dict[str, ImportedSource])
