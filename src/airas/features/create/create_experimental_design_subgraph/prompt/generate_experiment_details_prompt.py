generate_experiment_details_prompt = """\
You are a cutting-edge AI researcher. Based on the new method described in # New Methods and the experimental policy outlined in # Experiment Strategy, please follow the instructions below and provide a detailed elaboration of the experimental content.

# Instructions
- For each experiment listed in “Experiment Strategy,” output the detailed experimental plan.
- Design the details of each experiment assuming the execution environment specified in “Experimental Environment.”
- The experimental details should include the following:
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
- In addition, describe the experimental details as thoroughly as possible. It is acceptable if the output is long.
- Include example experimental code if available.
- Avoid excessive redundancy across experiments. When a single experiment can cover multiple validation items, integrate them appropriately.

{% if consistency_feedback %}
- **Important**: Address the following feedback from previous experimental consistency evaluation:
{{ consistency_feedback }}
- Specifically improve the experimental details to resolve these consistency issues.
{% endif %}

# Experimental Environment
{{ runner_type_prompt }}

# Current Research Method (Target for Experiment Design)
{{ new_method.method }}

# Experiment Strategy
{{ new_method.experimental_design.experiment_strategy }}

---
# Reference Information from Previous Iteration
{% if previous_method and previous_method.experimental_design %}
**Previous Experimental Design**:
- Strategy: {{ previous_method.experimental_design.experiment_strategy }}
- Details: {{ previous_method.experimental_design.experiment_details }}

{% if generated_file_contents %}
**Previous Generated Code Files**:
{% for filename, content in generated_file_contents.items() %}
### {{ filename }}
```python
{{ content }}
```
{% endfor %}
{% endif %}

Build upon what worked and address what didn't work to improve the consistency score.
{% else %}
*No previous iteration available*
{% endif %}
---"""
