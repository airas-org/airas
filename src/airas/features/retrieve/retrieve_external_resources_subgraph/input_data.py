from airas.types.research_hypothesis import ExperimentalDesign, ResearchHypothesis

retrieve_external_resources_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="A novel approach to image classification using vision transformers",
        experimental_design=ExperimentalDesign(
            experiment_strategy="Compare our method against baseline approaches",
            experiment_details="Evaluate on standard datasets with multiple metrics",
            expected_models=["ResNet-50", "Vision Transformer", "BERT"],
            expected_datasets=["CIFAR-10", "ImageNet", "IMDB"],
        ),
    )
}
