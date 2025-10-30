evaluate_experimental_design_prompt = """\
You are an expert in machine learning research and experimental design.

Your task is to evaluate the current experimental design based on the experimental results and analysis, and provide constructive feedback for iterative improvement.

# Current Experimental Design

## Experiment Summary
{{ new_method.experimental_design.experiment_summary }}

## Evaluation Metrics
{% for metric in new_method.experimental_design.evaluation_metrics %}
- {{ metric }}
{% endfor %}

## Proposed Method
{{ new_method.experimental_design.proposed_method }}

## Comparative Methods
{% for method in new_method.experimental_design.comparative_methods %}
- {{ method }}
{% endfor %}

{% if new_method.experimental_design.models_to_use %}
## Models Used
{% for model in new_method.experimental_design.models_to_use %}
- {{ model }}
{% endfor %}
{% endif %}

{% if new_method.experimental_design.datasets_to_use %}
## Datasets Used
{% for dataset in new_method.experimental_design.datasets_to_use %}
- {{ dataset }}
{% endfor %}
{% endif %}

{% if new_method.experimental_design.hyperparameters_to_search %}
## Hyperparameters to Search
{% for key, value in new_method.experimental_design.hyperparameters_to_search.items() %}
- {{ key }}: {{ value }}
{% endfor %}
{% endif %}

# Experimental Results and Analysis

{% if new_method.experimental_analysis %}
{% if new_method.experimental_analysis.analysis_report %}
## Analysis Report
{{ new_method.experimental_analysis.analysis_report }}
{% endif %}

{% if new_method.experimental_analysis.aggregated_metrics %}
## Aggregated Metrics
{{ new_method.experimental_analysis.aggregated_metrics }}
{% endif %}
{% endif %}

# Experiment Runs
{% if new_method.experiment_runs %}
{% for run in new_method.experiment_runs %}
## Run: {{ run.run_id }}
**Method**: {{ run.method_name }}
{% if run.model_name %}**Model**: {{ run.model_name }}{% endif %}
{% if run.dataset_name %}**Dataset**: {{ run.dataset_name }}{% endif %}

{% if run.results %}
{% if run.results.metrics_data %}
**Metrics**:
{{ run.results.metrics_data }}
{% endif %}
{% endif %}

{% endfor %}
{% endif %}

# Task

Based on the experimental results and analysis above, evaluate whether the current experimental design is optimal or needs refinement. Provide specific, actionable feedback for improving the experimental design in the following aspects:

1. **Evaluation Metrics**: Are the current metrics sufficient and appropriate? Should we add or remove any metrics?
2. **Comparative Methods**: Are the baseline methods appropriate for demonstrating the value of the proposed method? Should we add more competitive baselines or remove ineffective ones?
3. **Models**: Are the selected models appropriate? Should we test on larger/smaller models or different architectures?
4. **Datasets**: Do the datasets effectively demonstrate the method's strengths? Should we add more challenging or diverse datasets?
5. **Hyperparameters**: Did the hyperparameter search cover the important parameters? Should we expand or narrow the search space?

**Important**:
- Only suggest design improvements if there are clear issues or opportunities for enhancement based on the results.
- If the current design is already comprehensive and the results are satisfactory, you can indicate that no major changes are needed.
- Focus on changes that would strengthen the scientific validity or demonstrate the method's effectiveness more convincingly.

Please provide your evaluation as "design_feedback". If no significant improvements are needed, state that the current design is adequate.
"""
