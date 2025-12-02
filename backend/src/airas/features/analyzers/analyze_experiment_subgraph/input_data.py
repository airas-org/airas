from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_design import (
    EvaluationMetric,
    ExperimentalDesign,
    MethodConfig,
    TrainingConfig,
)
from airas.types.experimental_results import ExperimentalResults
from airas.types.research_hypothesis import ResearchHypothesis

analyze_experiment_subgraph_input_data = {
    "research_hypothesis": ResearchHypothesis(
        open_problems="Current NLP models struggle with long-context understanding",
        method="Propose a hierarchical attention mechanism to improve long-context processing",
        experimental_setup="Compare the proposed method against standard Transformer on long document classification tasks",
        primary_metric="Accuracy on documents longer than 2000 tokens",
        experimental_code="Implement hierarchical attention in PyTorch and evaluate on IMDb and Yelp datasets",
        expected_result="Improved accuracy by 3-5% on long documents compared to baseline",
        expected_conclusion="Hierarchical attention effectively captures long-range dependencies",
    ),
    "experimental_design": ExperimentalDesign(
        experiment_summary="Evaluate hierarchical attention mechanism on long document classification",
        evaluation_metrics=[
            EvaluationMetric(
                name="Accuracy",
                description="Classification accuracy on test set, measuring percentage of correctly classified documents",
            ),
            EvaluationMetric(
                name="F1 Score",
                description="Macro F1 score across all classes to handle potential class imbalance",
            ),
        ],
        models_to_use=["bert-base-uncased", "roberta-base"],
        datasets_to_use=["imdb", "yelp_polarity"],
        proposed_method=MethodConfig(
            method_name="HierarchicalAttention",
            description="Hierarchical attention mechanism with chunk-level and document-level attention",
            training_config=TrainingConfig(
                learning_rate=2e-5,
                batch_size=16,
                epochs=5,
                optimizer="adamw",
                warmup_steps=500,
                weight_decay=0.01,
            ),
        ),
        comparative_methods=[
            MethodConfig(
                method_name="StandardTransformer",
                description="Standard Transformer baseline without hierarchical mechanism",
                training_config=TrainingConfig(
                    learning_rate=2e-5,
                    batch_size=16,
                    epochs=5,
                    optimizer="adamw",
                ),
            ),
        ],
    ),
    "experiment_code": ExperimentCode(
        train_py="# Training script placeholder",
        evaluate_py="# Evaluation script placeholder",
        preprocess_py="# Preprocessing script placeholder",
        model_py="# Model definition placeholder",
        main_py="# Main execution script placeholder",
        pyproject_toml="# Project configuration placeholder",
        config_yaml="# Config placeholder",
    ),
    "experimental_results": ExperimentalResults(
        metrics_data={
            "HierarchicalAttention_imdb": {
                "accuracy": 0.892,
                "f1_score": 0.888,
            },
            "StandardTransformer_imdb": {
                "accuracy": 0.854,
                "f1_score": 0.851,
            },
            "HierarchicalAttention_yelp": {
                "accuracy": 0.901,
                "f1_score": 0.898,
            },
            "StandardTransformer_yelp": {
                "accuracy": 0.867,
                "f1_score": 0.863,
            },
        },
        figures=["confusion_matrix.png", "attention_heatmap.png"],
    ),
}
