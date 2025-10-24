analytic_node_prompt = """\
You are an expert in machine learning research.

Your task is to analyze the experimental results and generate a comprehensive analysis report that demonstrates the effectiveness of the proposed method.

# Instructions
1. Analyze the experimental results from all experiments
2. Synthesize findings to demonstrate the overall effectiveness of the proposed method
3. Highlight how the proposed method outperforms baselines
4. Reference specific metrics and experimental outcomes
5. Generate a detailed analysis report

# Proposed Method
{{ new_method.method }}

{% if new_method.experimental_design %}
# Experimental Design

## Experiment Summary
{{ new_method.experimental_design.experiment_summary }}

## Evaluation Metrics
{% for metric in new_method.experimental_design.evaluation_metrics %}
- {{ metric }}
{% endfor %}

## Proposed Method Details
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
{% endif %}

# Experimental Analysis
{% if new_method.experimental_analysis %}
{% if new_method.experimental_analysis.aggregated_metrics %}
## Aggregated Metrics
{{ new_method.experimental_analysis.aggregated_metrics }}
{% endif %}

{% if new_method.experimental_analysis.comparison_figures %}
## Comparison Figures
{% for figure in new_method.experimental_analysis.comparison_figures %}
- {{ figure }}
{% endfor %}
{% endif %}
{% endif %}

# Experiment Runs and Results
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

{% if run.results.figures %}
**Figures**: {{ run.results.figures | join(', ') }}
{% endif %}
{% endif %}

{% endfor %}
{% else %}
No experimental results available yet.
{% endif %}

# Task
Please summarize the experimental results in detail as an "analysis_report", based on the experimental setup and outcomes. Also, include whether the new method demonstrates a clear advantage over baselines.
"""
