generate_experiments_prompt = """\
You are a cutting-edge AI researcher. Based on the new method described in # New Methods and the experimental policy outlined in # Experiment Strategy, please generate {{ num_experiments }} distinct Experiment objects.

# Instructions
- Generate {{ num_experiments }} major experimental lines (Experiment objects) based on the experimental strategy.
- Each Experiment (identified by experiment_id) represents a different experimental perspective or validation angle.
- Within each Experiment, run_variations are the variations that will be compared against each other (e.g., ["baseline", "proposed"], ["full-method", "ablation-A", "ablation-B"]).
- Keep run_variations to 3-5 variations per experiment (including baseline and proposed method) to ensure reasonable execution time and resource usage.
- Each Experiment should:
    - Have a unique experiment_id (e.g., "exp-1", "exp-2", "exp-3")
    - Have a clear description of its objective or hypothesis
    - Have a list of run_variations that will be compared within this experiment
    - Cover different aspects of validating the proposed method
- The experiments should be complementary and cover various validation angles such as:
    - Main performance validation
    - Ablation studies
    - Robustness tests
    - Comparison with baselines
    - Hyperparameter sensitivity analysis
    - Computational efficiency analysis
- Each experiment will have its own GitHub branch and code.
- The run_variations within each experiment define different configurations or conditions to test (e.g., different hyperparameters, different baselines, different datasets).

- Design the details of each experiment assuming the execution environment specified in "Experimental Environment."
- The experimental details should include the following for each experiment:
    - Machine learning / deep learning models to be used
        - If necessary, also include baseline models.
    - Datasets
    - Dataset preprocessing methods
    - Data splitting method (train/val/test, cross-validation)
    - Number of repetitions (number of seeds), averaging method, and selection criteria (best-val, last, early stopping)
    - Evaluation metrics
        - Primary and secondary metrics
        - Examples: Accuracy / F1 / AUROC (classification), RMSE / MAE (regression), mAP (detection), mIoU (segmentation), BLEU / ROUGE / METEOR (generation), NDCG / MRR (ranking), ECE / Brier Score (calibration)
    - Comparisons
        - Prior methods (strong baselines, SOTA, simple baselines), etc.
        - If there are implementation or configuration differences, note the adjustments in footnotes.
    - Methods for analyzing important hyperparameters (e.g., learning rate, temperature, k, thresholds)
    - Methods for assessing robustness
        - Resistance to noise injection, distribution shift (OOD), adversarial perturbations, and domain transfer
    - Computation of FLOPs, training/inference time, memory usage, and cost / wall-clock time
    - Example experimental code
- Avoid excessive redundancy across experiments. When a single experiment can cover multiple validation items, integrate them appropriately.
- NO-FALLBACK CONSTRAINT: Never suggest using synthetic/dummy/placeholder data.
- Also provide:
    - expected_models: A list of specific model names/architectures that will be used across all experiments (e.g., ["ResNet-50", "BERT-base", "GPT-3.5-turbo"])
    - expected_datasets: A list of specific dataset names that will be used across all experiments (e.g., ["CIFAR-10", "ImageNet", "IMDB Reviews"])

## Output Format
Please provide:
- experiments: A list of {{ num_experiments }} Experiment objects, each with:
    - experiment_id: Unique identifier
    - run_variations: List of variation names/identifiers for this experiment
    - description: Detailed description including all aspects mentioned in the instructions
- expected_models: List of model names/architectures
- expected_datasets: List of dataset names

# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

# Experiment Strategy
{{ new_method.experimental_design.experiment_strategy }}

---
{% if consistency_feedback %}
- **Important**: Address the following feedback from previous experimental consistency evaluation:
{{ consistency_feedback }}
- Specifically improve the experimental design to resolve these consistency issues.
{% endif %}

# Reference Information from Previous Iteration
{% if new_method.iteration_history %}
**Previous Experimental Design**:
- Strategy: {{ new_method.iteration_history[-1].experimental_design.experiment_strategy }}
- Experiments: {{ new_method.iteration_history[-1].experimental_design.experiments | tojson }}

Build upon what worked and address what didn't work to improve the consistency score.
{% endif %}
"""
