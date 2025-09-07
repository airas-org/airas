# import logging

# from jinja2 import Environment
# from pydantic import BaseModel

# from airas.features.retrieve.retrieve_external_resources_subgraph.prompt.select_relevant_resources_prompt import (
#     select_relevant_resources_prompt,
# )
# from airas.services.api_client.llm_client.llm_facade_client import (
#     LLM_MODEL,
#     LLMFacadeClient,
# )
# from airas.types.research_hypothesis import ResearchHypothesis

# logger = logging.getLogger(__name__)


# class SelectedResource(BaseModel):
#     title: str
#     url: str


# class LLMOutput(BaseModel):
#     selected_models: list[SelectedResource]
#     selected_datasets: list[SelectedResource]


# def select_relevant_resources(
#     llm_name: LLM_MODEL,
#     new_method: ResearchHypothesis,
#     huggingface_search_results: dict[str, list[dict[str, str]]],
#     prompt_template: str = select_relevant_resources_prompt,
#     client: LLMFacadeClient | None = None,
# ) -> dict[str, list[dict[str, str]]]:
#     client = client or LLMFacadeClient(llm_name=llm_name)

#     data = {
#         "new_method": new_method.model_dump(),
#         "huggingface_search_results": huggingface_search_results,
#     }

#     env = Environment()
#     template = env.from_string(prompt_template)
#     messages = template.render(data)

#     logger.info("Selecting relevant resources using LLM...")

#     output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)
#     if output is None:
#         raise ValueError("Error: No response from LLM in select_relevant_resources.")

#     selected_resources = {
#         "models": [
#             {
#                 "title": resource["title"],
#                 "url": resource["url"],
#                 "resource_type": "model",
#             }
#             for resource in output["selected_models"]
#         ],
#         "datasets": [
#             {
#                 "title": resource["title"],
#                 "url": resource["url"],
#                 "resource_type": "dataset",
#             }
#             for resource in output["selected_datasets"]
#         ],
#     }

#     logger.info(
#         f"Selected {len(selected_resources['models'])} models and "
#         f"{len(selected_resources['datasets'])} datasets"
#     )

#     return selected_resources
