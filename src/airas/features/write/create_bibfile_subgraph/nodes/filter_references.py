import json
from typing import Annotated

from jinja2 import Environment
from pydantic import BaseModel, Field

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.save_prompt import save_io_on_github


class FilteredReferencesOutput(BaseModel):
    selected_reference_indices: Annotated[
        list[int],
        Field(description="List of indices of selected references from reference_list"),
    ]


def filter_references(
    llm_name: LLM_MODEL,
    prompt_template: str,
    research_study_list: list[ResearchStudy],
    reference_study_list: list[ResearchStudy],
    new_method: ResearchHypothesis,
    github_repository_info: GitHubRepositoryInfo,
    max_results: int = 30,
    client: LLMFacadeClient | None = None,
) -> list[ResearchStudy]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    data = {
        "research_study_list": [study.model_dump() for study in research_study_list],
        "reference_study_list": [study.model_dump() for study in reference_study_list],
        "research_hypothesis": new_method.model_dump(),
        "max_results": max_results,
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    output, _ = client.structured_outputs(
        message=messages, data_model=FilteredReferencesOutput
    )
    if output is None:
        raise ValueError("Error: No response from LLM in filter_references.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_bibfile_subgraph",
        node_name="filter_references",
        llm_name=llm_name,
    )
    selected_indices = output["selected_reference_indices"]
    filtered_references = [
        reference_study_list[i]
        for i in selected_indices
        if 0 <= i < len(reference_study_list)
    ]

    return filtered_references


def main():
    from airas.features.write.create_bibfile_subgraph.prompt.filter_references_prompt import (
        filter_references_prompt,
    )

    llm_name = "gemini-2.0-flash-001"

    research_study_list = [
        {
            "title": "Deep Learning for Natural Language Processing",
            "full_text": "This paper presents a comprehensive study on deep learning methods for NLP tasks including sentiment analysis, machine translation, and text classification.",
            "abstract": "Deep learning has revolutionized NLP...",
        }
    ]

    reference_study_list = [
        {
            "title": "Attention Is All You Need",
            "full_text": "The Transformer architecture has become the foundation of modern NLP models. This paper introduces the self-attention mechanism...",
            "abstract": "We propose a new simple network architecture...",
            "authors": ["Vaswani", "Shazeer"],
            "year": 2017,
        },
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "full_text": "BERT represents words bidirectionally using transformers. We show that pre-training deep bidirectional representations...",
            "abstract": "We introduce a new language representation model...",
            "authors": ["Devlin", "Chang"],
            "year": 2018,
        },
        {
            "title": "Computer Vision and Pattern Recognition",
            "full_text": "This paper focuses on image classification using convolutional neural networks for computer vision tasks...",
            "abstract": "Computer vision methods for image processing...",
            "authors": ["Smith", "Johnson"],
            "year": 2019,
        },
    ]

    research_hypothesis = "Deep learning models with attention mechanisms significantly improve performance on natural language understanding tasks compared to traditional approaches."

    try:
        filtered_refs = filter_references(
            llm_name=llm_name,
            prompt_template=filter_references_prompt,
            research_study_list=research_study_list,
            reference_study_list=reference_study_list,
            research_hypothesis=research_hypothesis,
            max_results=2,
        )

        print(
            f"Filtered {len(filtered_refs)} references from {len(reference_study_list)} total:"
        )
        for i, ref in enumerate(filtered_refs):
            print(f"{i + 1}. {ref.get('title', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
