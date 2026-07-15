decide_experiment_cycle_prompt = """\
You are an AI researcher deciding the next action for an experiment cycle.

Based on the full experiment history and the latest analysis, decide whether to:
- **scale_up**: The pilot results are promising. Run the same design at main (full) scale.
- **redesign**: The results indicate the current approach needs changes. Provide a design_instruction describing what should be modified.
- **complete**: The main experiment has been successfully completed and the results are satisfactory.
- **abort**: The experiment is fundamentally flawed or infeasible. No further cycles should be attempted.

# Research Hypothesis
{{ research_hypothesis }}

# Experiment History
{% for cycle in experiment_history.cycles %}
## Cycle {{ loop.index }}
- Stage: {{ cycle.run_stage.value }}
- Design:
  - Summary: {{ cycle.experimental_design.experiment_summary }}
  - Models: {{ cycle.experimental_design.models_to_use }}
  - Datasets: {{ cycle.experimental_design.datasets_to_use }}
  - Proposed method: {{ cycle.experimental_design.proposed_method.method_name }} - {{ cycle.experimental_design.proposed_method.description }}
  {% if cycle.experimental_design.comparative_methods %}- Comparative methods: {% for m in cycle.experimental_design.comparative_methods %}{{ m.method_name }}{% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
  - Evaluation metrics: {% for m in cycle.experimental_design.evaluation_metrics %}{{ m.name }}{% if not loop.last %}, {% endif %}{% endfor %}
{% if cycle.experimental_results %}- Results:
  {% if cycle.experimental_results.stdout %}  - Stdout (summary): {{ cycle.experimental_results.stdout[:500] }}{% endif %}
  {% if cycle.experimental_results.metrics_data %}  - Metrics: {{ cycle.experimental_results.metrics_data }}{% endif %}
{% endif %}
{% if cycle.experimental_analysis %}- Analysis: {{ cycle.experimental_analysis.analysis_report }}
{% endif %}
{% endfor %}

# Decision Guidelines
- If the latest cycle was pilot and results look reasonable, prefer **scale_up**.
- If the latest cycle was main and results are satisfactory, choose **complete**.
- If results show clear issues (wrong approach, poor metrics, unexpected behavior), choose **redesign** and provide a specific design_instruction explaining what to change and why.
- Only choose **abort** if the problem is fundamentally intractable or resources have been exhausted with no progress across multiple cycles.
- Consider the trend across all cycles, not just the latest one.

# Output Format
- action: One of "scale_up", "redesign", "complete", or "abort"
- reasoning: A clear explanation of why this action was chosen, referencing specific results or trends
- design_instruction: Required only when action is "redesign". A specific instruction describing what should be changed in the experimental design and why."""
