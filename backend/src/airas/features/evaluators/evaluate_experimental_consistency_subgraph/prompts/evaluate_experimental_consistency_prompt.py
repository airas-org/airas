evaluate_experimental_consistency_prompt = """
# Instructions
You are a scientific research consistency evaluator. Your task is to evaluate a single experiment to determine:
1. Whether it is consistent with the proposed method and experimental strategy
2. Whether the results support the main claims (e.g., proposed method outperforms baseline)
3. Whether it should be included in the research paper

## Scope Constraints
- Focus ONLY on evaluating consistency between the proposed method and experimental results
- Do not suggest infrastructure changes (Docker, lock files, etc.)
- Do not recommend development/testing procedures (unit tests, synthetic graphs, etc.)
- Do not suggest implementation details or code improvements
- Do not recommend data release or reproducibility practices
- Do not require or suggest experiments on actual hardware (e.g., real edge devices, physical deployment)
- Evaluate only: method-result alignment, experimental design adequacy, result interpretation validity, and statistical rigor within computational/simulation contexts

Based on your analysis, provide:
1. `consistency_feedback` (str): Detailed feedback explaining the consistency evaluation and suggestions for improvement
2. `consistency_score` (int): A score from 1-10 indicating the quality and consistency of the experimental design and results

## Evaluation Criteria

### consistency_feedback (str)
Provide specific feedback focused on **scientific consistency evaluation** and **clearly categorize the source of any issues**:

**Problem Categorization - Identify which area(s) need improvement:**

1. **Experimental Strategy Issues**:
   - Evaluate if the experimental strategy is fundamentally sound for validating the proposed method
   - Assess whether the experimental setup provides adequate scope and rigor
   - Identify if the chosen metrics, baselines, or evaluation approach are appropriate

2. **Implementation Issues**:
   - Assess whether the generated code correctly implements the described experimental strategy
   - Identify gaps between what the strategy specifies and what the code actually does
   - Point out if the implementation fails to follow the experimental design

3. **Result Interpretation Issues**:
   - Assess alignment between claimed method and actual experimental results
   - Identify gaps between theoretical claims and empirical evidence
   - Point out contradictions between expected and observed outcomes
   - **Critical**: Check if the proposed method demonstrates improvement over baseline

**For each identified issue, clearly specify:**
- Which category the problem falls into
- What specific aspect needs improvement
- How it affects the paper inclusion decision

### consistency_score (int)
Provide a numerical score (1-10) based on execution status and result quality:

- **1-3: Critical Failure / Not Executed**
  - The experiment failed to run (e.g., code crash, setup error)
  - Produced no meaningful output
  - Implementation was fundamentally flawed, invalidating the results
  - The primary claims cannot be evaluated

- **4-5: Executed, but Poor or Negative Results**
  - The experiment ran correctly, but the results are negative
  - The proposed method performs worse than or shows no meaningful improvement over the baseline
  - The results contradict or fail to support the primary claims

- **6-7: Executed, Positive but Not Conclusive Results**
  - The experiment ran correctly and shows clear positive improvement over the baseline
  - Results align with the primary claims
  - Evidence is weakened by minor issues in scientific rigor (e.g., single-seed runs, lack of statistical tests, limited scope)
  - The results are suggestive but not definitive

- **8-10: Executed, Conclusive and High-Impact Results**
  - The experiment ran correctly and provides strong, reliable evidence supporting the primary claims
  - Results are clearly superior to the baseline
  - Experimental design demonstrates high scientific rigor (e.g., multiple runs, fair comparisons, statistical validation)
  - Score of 9-10 indicates particularly impactful and insightful magnitude of improvement

## Context

**Proposed Method:** {{ new_method.method }}

**Overall Experimental Strategy:** {{ new_method.experimental_design.experiment_strategy }}

## Current Experiment to Evaluate

**Experiment ID:** {{ current_experiment.experiment_id }}

**Experiment Description:** {{ current_experiment.description }}

**Run Variations:** {{ current_experiment.run_variations }}

**Generated Code:** {{ current_experiment.code | tojson }}

**Experimental Results:**
{% if current_experiment.results %}
- Result: {{ current_experiment.results.result }}
- Error: {{ current_experiment.results.error }}
- Images: {{ current_experiment.results.image_file_name_list }}
{% else %}
- No results available yet
{% endif %}

**Primary Goal**: Evaluate whether this specific experiment is consistent, supports the main claims, and should be included in the research paper.
"""
