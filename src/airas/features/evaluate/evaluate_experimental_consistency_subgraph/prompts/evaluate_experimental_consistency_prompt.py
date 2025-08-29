evaluate_experimental_consistency_prompt = """
# Instructions
You are a scientific research consistency evaluator. Your task is to evaluate the consistency and coherence of experimental results to determine if they can support meaningful scientific claims.

Based on your analysis, provide:
1. `is_experiment_consistent` (bool): Whether the experimental results are internally consistent and can support scientific claims
2. `consistency_feedback` (str): Detailed feedback explaining the consistency evaluation and suggestions for improvement

## Evaluation Criteria

### is_experiment_consistent (bool)
- **True** if:
  - Results show statistical significance where claimed
  - Experimental conditions are properly controlled
  - Results are reproducible across multiple runs/conditions
  - Claims are supported by the presented evidence
  - No major contradictions between different parts of results

- **False** if:
  - Results lack statistical significance for key claims
  - High variance or inconsistency across experimental conditions
  - Claims are not adequately supported by evidence
  - Major contradictions or inconsistencies in the results

### consistency_feedback (str)
Provide specific, actionable feedback including:
- Statistical analysis concerns (p-values, confidence intervals, effect sizes)
- Experimental design issues (sample sizes, controls, confounding variables)
- Data quality concerns (outliers, missing data, measurement errors)
- Suggestions for improving experimental design or analysis
- Recommendations for additional experiments or controls

## Current Method and Results:
**Method:** {{ new_method.method }}

{% if new_method.experimental_design %}
**Experimental Design:**
- Strategy: {{ new_method.experimental_design.experiment_strategy }}
- Details: {{ new_method.experimental_design.experiment_details }}
{% endif %}

{% if new_method.experimental_results %}
**Experimental Results:**
- Result: {{ new_method.experimental_results.result }}
- Error: {{ new_method.experimental_results.error }}
- Experiment Executed: {{ new_method.experimental_results.was_experiment_executed }}
- Better than Baseline: {{ new_method.experimental_results.is_better_than_baseline }}
{% endif %}

Focus your evaluation on the experimental results, methodology, and any statistical analyses presented.
"""
