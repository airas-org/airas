from typing import Annotated, Sequence

from jinja2 import Environment
from pydantic import BaseModel, Field, create_model

from airas.typing.paper import CandidatePaperInfo
from airas.utils.api_client.llm_facade_client import LLM_MODEL, LLMFacadeClient


def _build_generated_query_model(n_queries: int) -> type[BaseModel]:
    fields = {f"generated_query_{i+1}": (str, ...) for i in range(n_queries)}
    return create_model("LLMOutput", **fields)

def generate_queries(
    llm_name: LLM_MODEL,
    prompt_template: str,
    paper_info: CandidatePaperInfo | dict[str, str],
    n_queries: Annotated[int | None, Field(gt=0)] = None, 
    previous_queries: list[str] | None = None, 
    dict_keys: Sequence[str] | None = None, 
    client: LLMFacadeClient | None = None, 
) -> list[str] | dict[str, str]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    if dict_keys:
        n_queries = len(dict_keys)

    if n_queries is None:
        raise ValueError("You must specify either `n_queries` or `dict_keys`.")

    data = {
        "paper_info": paper_info, 
        "previous_queries": previous_queries,
        "n_queries": n_queries,         
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    DynamicLLMOutput = _build_generated_query_model(n_queries)
    output, cost = client.structured_outputs(message=messages, data_model=DynamicLLMOutput)
    if output is None:
        raise ValueError("Error: No response from LLM in generate_queries_node.")
    
    if dict_keys:
        return {
            key: output[f"generated_query_{i+1}"] for i, key in enumerate(dict_keys)
        }
    return [output[f"generated_query_{i+1}"] for i in range(n_queries)]