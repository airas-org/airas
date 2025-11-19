analyze_experiment_prompt = """\
You are an expert in machine learning research.

Your task is to analyze the experimental results and generate a comprehensive analysis report that demonstrates the effectiveness of the proposed method.

# Instructions
1. Analyze the experimental results from all experiments
2. Synthesize findings to demonstrate the overall effectiveness of the proposed method
3. Highlight how the proposed method outperforms baselines
4. Reference specific metrics and experimental outcomes
5. Generate a detailed analysis report

# Hypothesis
{{ research_session.hypothesis }}

# Proposed Method
{{ research_session.current_iteration.method }}

{% if research_session.current_iteration.experimental_design %}
# Experimental Design

## Experiment Summary
{{ research_session.current_iteration.experimental_design.experiment_summary }}

## Evaluation Metrics
{% for metric in research_session.current_iteration.experimental_design.evaluation_metrics %}
- {{ metric }}
{% endfor %}

## Proposed Method Details
{{ research_session.current_iteration.experimental_design.proposed_method }}

## Comparative Methods
{% for method in research_session.current_iteration.experimental_design.comparative_methods %}
- {{ method }}
{% endfor %}

{% if research_session.current_iteration.experimental_design.models_to_use %}
## Models Used
{% for model in research_session.current_iteration.experimental_design.models_to_use %}
- {{ model }}
{% endfor %}
{% endif %}

{% if research_session.current_iteration.experimental_design.datasets_to_use %}
## Datasets Used
{% for dataset in research_session.current_iteration.experimental_design.datasets_to_use %}
- {{ dataset }}
{% endfor %}
{% endif %}
{% endif %}

# Experimental Analysis
{% if research_session.current_iteration.experimental_analysis %}
{% if research_session.current_iteration.experimental_analysis.aggregated_metrics %}
## Aggregated Metrics
{{ research_session.current_iteration.experimental_analysis.aggregated_metrics | tojson(indent=2) }}
{% endif %}

{% if research_session.current_iteration.experimental_analysis.comparison_figures %}
## Comparison Figures
{% for figure in research_session.current_iteration.experimental_analysis.comparison_figures %}
- {{ figure }}
{% endfor %}
{% endif %}
{% endif %}

# Experiment Runs and Results
{% if research_session.current_iteration.experiment_runs %}
{% for run in research_session.current_iteration.experiment_runs %}
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
