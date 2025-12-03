from fastapi import APIRouter

from api.schemas.bibfile import (
    GenerateBibfileSubgraphRequestBody,
    GenerateBibfileSubgraphResponseBody,
)
from src.airas.features.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)

router = APIRouter(prefix="/bibfile", tags=["bibfile"])


@router.post("/generations", response_model=GenerateBibfileSubgraphResponseBody)
async def generate_bibfile(
    request: GenerateBibfileSubgraphRequestBody,
) -> GenerateBibfileSubgraphResponseBody:
    result = await GenerateBibfileSubgraph().build_graph().ainvoke(request)
    return GenerateBibfileSubgraphResponseBody(
        references_bib=result["references_bib"],
        execution_time=result["execution_time"],
    )
