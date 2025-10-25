from contextlib import asynccontextmanager

from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.execution_cost import CostInfo, ExecutionCostList


@asynccontextmanager
async def track_execution_cost(
    execution_costs: ExecutionCostList,
    node_name: str,
    model_name: LLM_MODEL,
):
    def record(cost: dict[str, float]) -> None:
        execution_costs.append(
            CostInfo(
                node_name=node_name,
                model_name=model_name,
                input_cost=cost["input_cost"],
                output_cost=cost["output_cost"],
            )
        )

    yield record
