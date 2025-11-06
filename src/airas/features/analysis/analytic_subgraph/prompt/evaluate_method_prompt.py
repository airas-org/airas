evaluate_method_prompt = """\
You are an expert in machine learning research and methodology.

Your task is to evaluate the proposed research method based on experimental results and provide feedback to guide the next iteration toward more effective approaches.

{% if hypothesis_history %}
# Previous Method Iterations

The following methods have been tried in previous iterations:

{% for hypothesis in hypothesis_history %}
## Iteration {{ hypothesis.method_iteration_id }}

### Method
{{ hypothesis.method }}

{% if hypothesis.experimental_analysis and hypothesis.experimental_analysis.evaluation %}
### Previous Feedback
{{ hypothesis.experimental_analysis.evaluation.method_feedback }}
{% endif %}

{% if hypothesis.experimental_analysis and hypothesis.experimental_analysis.aggregated_metrics %}
### Results
{{ hypothesis.experimental_analysis.aggregated_metrics }}
{% endif %}

{% endfor %}
{% endif %}

# Current Proposed Method
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

**Context**: In this research workflow, multiple method variations with minor differences may be proposed and tested. Your role is to identify which variations performed better and provide feedback to guide the next iteration toward more effective approaches.

Analyze the experimental results and provide specific, actionable feedback for improving or refining the research method:

1. **Performance Analysis**:
   - If multiple method variations were tested, which performed best? Why?
   - Identify the specific characteristics or design choices that led to better performance

2. **Direction for Improvement**:
   - Based on the results, what direction should the method move toward?
   - If variation A outperformed variation B, what does this suggest about the underlying principles?
   - Should certain aspects be emphasized more or less in the next iteration?

3. **Methodological Refinement**:
   - Are there fundamental issues with the current approach that need addressing?
   - Should the method be reformulated to capitalize on the insights from successful variations?
   - Are there unexplored variations in the promising direction?

4. **Theoretical Insights**:
   - What do the results reveal about why certain approaches work better?
   - Are there implicit assumptions that should be reconsidered?

**Important**:
- Focus on extracting insights from the comparative performance of different variations
- Provide concrete guidance on which direction to explore in the next iteration
- If one variation clearly outperforms others, explain why and suggest how to further develop in that direction
- If no significant improvements are needed, state that the current method is effective

Please provide your evaluation as "method_feedback" with specific recommendations for the next iteration.
"""
