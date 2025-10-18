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

# Experimental Strategy
{{ new_method.experimental_design.experiment_strategy }}

# Experiments and Results
{% for experiment in new_method.experimental_design.experiments %}
{% if experiment.evaluation and experiment.evaluation.is_selected_for_paper %}
## Experiment: {{ experiment.experiment_id }}
**Description**: {{ experiment.description }}
**Run Variations**: {{ experiment.run_variations }}

**Code**:
{{ experiment.code | tojson }}

{% if experiment.results %}
**Results**: {{ experiment.results.result }}
{% if experiment.results.error %}
**Errors**: {{ experiment.results.error }}
{% endif %}
{% if experiment.results.image_file_name_list %}
**Figures**: {{ experiment.results.image_file_name_list | join(', ') }}
{% endif %}
{% endif %}

{% endif %}
{% endfor %}

# Task
Please summarize the experimental results in detail as an "analysis_report", based on the experimental setup and outcomes. Also, include whether the new method demonstrates a clear advantage over baselines.
"""
