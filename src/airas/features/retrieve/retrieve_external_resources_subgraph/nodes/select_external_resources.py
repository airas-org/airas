import json
import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.retrieve.retrieve_external_resources_subgraph.prompt.select_external_resources_prompt import (
    select_external_resources_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


class SelectedResource(BaseModel):
    title: str


class LLMOutput(BaseModel):
    selected_models: list[SelectedResource]
    selected_datasets: list[SelectedResource]


def select_external_resources(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    huggingface_search_results: dict[str, list[dict[str, str]]],
    prompt_template: str = select_external_resources_prompt,
    client: LLMFacadeClient | None = None,
) -> ResearchHypothesis:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(
        {
            "new_method": new_method.model_dump(),
            "huggingface_search_results": huggingface_search_results,
        }
    )

    logger.info("Selecting relevant resources using LLM...")

    output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)
    if output is None:
        raise ValueError("Error: No response from LLM in select_external_resources.")

    # Create lookup maps for original resources
    models_map = {
        item["title"]: item for item in huggingface_search_results.get("models", [])
    }
    datasets_map = {
        item["title"]: item for item in huggingface_search_results.get("datasets", [])
    }

    selected_resources = {
        "models": [
            models_map[resource["title"]]
            for resource in output["selected_models"]
            if resource["title"] in models_map
        ],
        "datasets": [
            datasets_map[resource["title"]]
            for resource in output["selected_datasets"]
            if resource["title"] in datasets_map
        ],
    }

    logger.info(
        f"Selected {len(selected_resources['models'])} models and "
        f"{len(selected_resources['datasets'])} datasets"
    )

    # TODO: Consider defining a dedicated type for external_resources instead of using str
    # Currently storing as JSON string, but could benefit from structured typing

    external_resources_str = json.dumps(selected_resources, indent=2)
    new_method.experimental_design.external_resources = external_resources_str

    return new_method


if __name__ == "__main__":
    huggingface_search_results = {
        "models": [
            {
                "title": "facebook/detr-resnet-50",
                "link": "https://huggingface.co/facebook/detr-resnet-50",
                "search_query": "ResNet-50",
            },
            {
                "title": "TanmayTomar/chest-xray-resnet50",
                "link": "https://huggingface.co/TanmayTomar/chest-xray-resnet50",
                "search_query": "ResNet-50",
            },
            {
                "title": "Axon/resnet50-v1",
                "link": "https://huggingface.co/Axon/resnet50-v1",
                "search_query": "ResNet-50",
            },
            {
                "title": "Francesco/resnet50-224-1k",
                "link": "https://huggingface.co/Francesco/resnet50-224-1k",
                "search_query": "ResNet-50",
            },
            {
                "title": "Francesco/resnet50",
                "link": "https://huggingface.co/Francesco/resnet50",
                "search_query": "ResNet-50",
            },
            {
                "title": "aychang/fasterrcnn-resnet50-cpu",
                "link": "https://huggingface.co/aychang/fasterrcnn-resnet50-cpu",
                "search_query": "ResNet-50",
            },
            {
                "title": "facebook/detr-resnet-50-dc5-panoptic",
                "link": "https://huggingface.co/facebook/detr-resnet-50-dc5-panoptic",
                "search_query": "ResNet-50",
            },
            {
                "title": "facebook/detr-resnet-50-dc5",
                "link": "https://huggingface.co/facebook/detr-resnet-50-dc5",
                "search_query": "ResNet-50",
            },
            {
                "title": "facebook/detr-resnet-50-panoptic",
                "link": "https://huggingface.co/facebook/detr-resnet-50-panoptic",
                "search_query": "ResNet-50",
            },
            {
                "title": "glasses/cse_resnet50",
                "link": "https://huggingface.co/glasses/cse_resnet50",
                "search_query": "ResNet-50",
            },
            {
                "title": "jeffboudier/vision-transformers-spain-or-italy-fan",
                "link": "https://huggingface.co/jeffboudier/vision-transformers-spain-or-italy-fan",
                "search_query": "Vision Transformer",
            },
            {
                "title": "keras-io/video-vision-transformer",
                "link": "https://huggingface.co/keras-io/video-vision-transformer",
                "search_query": "Vision Transformer",
            },
            {
                "title": "shivkumarganesh/vision-transformer-fmri-classification-ft",
                "link": "https://huggingface.co/shivkumarganesh/vision-transformer-fmri-classification-ft",
                "search_query": "Vision Transformer",
            },
            {
                "title": "shivkumarganesh/vision_transformer_fmri_classification_ft",
                "link": "https://huggingface.co/shivkumarganesh/vision_transformer_fmri_classification_ft",
                "search_query": "Vision Transformer",
            },
            {
                "title": "pablorodriper/video-vision-transformer",
                "link": "https://huggingface.co/pablorodriper/video-vision-transformer",
                "search_query": "Vision Transformer",
            },
            {
                "title": "Ajibola/Pathway_Vision_Transformer",
                "link": "https://huggingface.co/Ajibola/Pathway_Vision_Transformer",
                "search_query": "Vision Transformer",
            },
            {
                "title": "haiderAI/vision_modelvision_Transformer_plant_disease_detetcion",
                "link": "https://huggingface.co/haiderAI/vision_modelvision_Transformer_plant_disease_detetcion",
                "search_query": "Vision Transformer",
            },
            {
                "title": "haiderAI/vision-transformer-rice-disease-detection",
                "link": "https://huggingface.co/haiderAI/vision-transformer-rice-disease-detection",
                "search_query": "Vision Transformer",
            },
            {
                "title": "ArSenic04/Image-Classification-vision-transformer",
                "link": "https://huggingface.co/ArSenic04/Image-Classification-vision-transformer",
                "search_query": "Vision Transformer",
            },
            {
                "title": "KhalfounMehdi/vision_transformer_mura_model",
                "link": "https://huggingface.co/KhalfounMehdi/vision_transformer_mura_model",
                "search_query": "Vision Transformer",
            },
            {
                "title": "google-bert/bert-base-uncased",
                "link": "https://huggingface.co/google-bert/bert-base-uncased",
                "search_query": "BERT",
            },
            {
                "title": "kaunista/style-bert-vits2-Anneli",
                "link": "https://huggingface.co/kaunista/style-bert-vits2-Anneli",
                "search_query": "BERT",
            },
            {
                "title": "google-bert/bert-base-chinese",
                "link": "https://huggingface.co/google-bert/bert-base-chinese",
                "search_query": "BERT",
            },
            {
                "title": "Davlan/bert-base-multilingual-cased-ner-hrl",
                "link": "https://huggingface.co/Davlan/bert-base-multilingual-cased-ner-hrl",
                "search_query": "BERT",
            },
            {
                "title": "klue/bert-base",
                "link": "https://huggingface.co/klue/bert-base",
                "search_query": "BERT",
            },
            {
                "title": "nlpaueb/legal-bert-base-uncased",
                "link": "https://huggingface.co/nlpaueb/legal-bert-base-uncased",
                "search_query": "BERT",
            },
            {
                "title": "Xenova/bert-base-multilingual-cased-ner-hrl",
                "link": "https://huggingface.co/Xenova/bert-base-multilingual-cased-ner-hrl",
                "search_query": "BERT",
            },
            {
                "title": "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
                "link": "https://huggingface.co/microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
                "search_query": "BERT",
            },
            {
                "title": "logasanjeev/emotions-analyzer-bert",
                "link": "https://huggingface.co/logasanjeev/emotions-analyzer-bert",
                "search_query": "BERT",
            },
            {
                "title": "KBLab/bert-base-swedish-cased",
                "link": "https://huggingface.co/KBLab/bert-base-swedish-cased",
                "search_query": "BERT",
            },
        ],
        "datasets": [
            {
                "title": "uoft-cs/cifar10",
                "link": "https://huggingface.co/datasets/uoft-cs/cifar10",
                "search_query": "CIFAR-10",
            },
            {
                "title": "uoft-cs/cifar100",
                "link": "https://huggingface.co/datasets/uoft-cs/cifar100",
                "search_query": "CIFAR-10",
            },
            {
                "title": "rafay/upside_down_detection_cifar100",
                "link": "https://huggingface.co/datasets/rafay/upside_down_detection_cifar100",
                "search_query": "CIFAR-10",
            },
            {
                "title": "student/CIFAR-10",
                "link": "https://huggingface.co/datasets/student/CIFAR-10",
                "search_query": "CIFAR-10",
            },
            {
                "title": "arize-ai/cifar10_quality_drift",
                "link": "https://huggingface.co/datasets/arize-ai/cifar10_quality_drift",
                "search_query": "CIFAR-10",
            },
            {
                "title": "HuggingFaceM4/cifar10-Dummy",
                "link": "https://huggingface.co/datasets/HuggingFaceM4/cifar10-Dummy",
                "search_query": "CIFAR-10",
            },
            {
                "title": "djghosh/wds_vtab-cifar100_test",
                "link": "https://huggingface.co/datasets/djghosh/wds_vtab-cifar100_test",
                "search_query": "CIFAR-10",
            },
            {
                "title": "djghosh/wds_cifar10_test",
                "link": "https://huggingface.co/datasets/djghosh/wds_cifar10_test",
                "search_query": "CIFAR-10",
            },
            {
                "title": "graphs-datasets/CIFAR10",
                "link": "https://huggingface.co/datasets/graphs-datasets/CIFAR10",
                "search_query": "CIFAR-10",
            },
            {
                "title": "Dahoas/unet-cifar10-32",
                "link": "https://huggingface.co/datasets/Dahoas/unet-cifar10-32",
                "search_query": "CIFAR-10",
            },
            {
                "title": "ILSVRC/imagenet-1k",
                "link": "https://huggingface.co/datasets/ILSVRC/imagenet-1k",
                "search_query": "ImageNet",
            },
            {
                "title": "zh-plus/tiny-imagenet",
                "link": "https://huggingface.co/datasets/zh-plus/tiny-imagenet",
                "search_query": "ImageNet",
            },
            {
                "title": "clane9/imagenet-100",
                "link": "https://huggingface.co/datasets/clane9/imagenet-100",
                "search_query": "ImageNet",
            },
            {
                "title": "benjamin-paine/imagenet-1k-256x256",
                "link": "https://huggingface.co/datasets/benjamin-paine/imagenet-1k-256x256",
                "search_query": "ImageNet",
            },
            {
                "title": "Lucasdegeorge/ImageNet_TA_IA",
                "link": "https://huggingface.co/datasets/Lucasdegeorge/ImageNet_TA_IA",
                "search_query": "ImageNet",
            },
            {
                "title": "nateraw/imagenette",
                "link": "https://huggingface.co/datasets/nateraw/imagenette",
                "search_query": "ImageNet",
            },
            {
                "title": "dandelin/imagenet",
                "link": "https://huggingface.co/datasets/dandelin/imagenet",
                "search_query": "ImageNet",
            },
            {
                "title": "student/ImageNet-64",
                "link": "https://huggingface.co/datasets/student/ImageNet-64",
                "search_query": "ImageNet",
            },
            {
                "title": "mrm8488/ImageNet1K-val",
                "link": "https://huggingface.co/datasets/mrm8488/ImageNet1K-val",
                "search_query": "ImageNet",
            },
            {
                "title": "mrm8488/ImageNet1K-train",
                "link": "https://huggingface.co/datasets/mrm8488/ImageNet1K-train",
                "search_query": "ImageNet",
            },
            {
                "title": "stanfordnlp/imdb",
                "link": "https://huggingface.co/datasets/stanfordnlp/imdb",
                "search_query": "IMDB",
            },
            {
                "title": "mathigatti/spanish_imdb_synopsis",
                "link": "https://huggingface.co/datasets/mathigatti/spanish_imdb_synopsis",
                "search_query": "IMDB",
            },
            {
                "title": "mirfan899/imdb_urdu_reviews",
                "link": "https://huggingface.co/datasets/mirfan899/imdb_urdu_reviews",
                "search_query": "IMDB",
            },
            {
                "title": "Lucylulu/imdb",
                "link": "https://huggingface.co/datasets/Lucylulu/imdb",
                "search_query": "IMDB",
            },
            {
                "title": "Recognai/imdb_spacy-ner",
                "link": "https://huggingface.co/datasets/Recognai/imdb_spacy-ner",
                "search_query": "IMDB",
            },
            {
                "title": "SetFit/imdb",
                "link": "https://huggingface.co/datasets/SetFit/imdb",
                "search_query": "IMDB",
            },
            {
                "title": "rubrix/imdb_spacy-ner",
                "link": "https://huggingface.co/datasets/rubrix/imdb_spacy-ner",
                "search_query": "IMDB",
            },
            {
                "title": "victor/autonlp-data-imdb-reviews-sentiment",
                "link": "https://huggingface.co/datasets/victor/autonlp-data-imdb-reviews-sentiment",
                "search_query": "IMDB",
            },
            {
                "title": "w11wo/imdb-javanese",
                "link": "https://huggingface.co/datasets/w11wo/imdb-javanese",
                "search_query": "IMDB",
            },
            {
                "title": "yxchar/imdb-tlm",
                "link": "https://huggingface.co/datasets/yxchar/imdb-tlm",
                "search_query": "IMDB",
            },
        ],
    }
    from airas.types.research_hypothesis import ExperimentalDesign

    new_method = ResearchHypothesis(
        method="A novel approach to image classification using vision transformers",
        experimental_design=ExperimentalDesign(
            expected_models=["ResNet-50", "Vision Transformer", "BERT"],
            expected_datasets=["CIFAR-10", "ImageNet", "IMDB"],
        ),
    )
    result = select_external_resources(
        llm_name="gpt-5-mini-2025-08-07",
        new_method=new_method,
        huggingface_search_results=huggingface_search_results,
    )
    print(f"result: {result}")
