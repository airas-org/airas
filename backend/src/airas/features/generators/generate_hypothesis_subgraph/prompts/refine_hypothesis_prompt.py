refine_hypothesis_prompt = """\
You are an accomplished researcher in the field of machine learning. Based on the instructions below, please refine the research hypothesis provided in "Hypothesis Info" to make it more novel and academically as well as socially valuable.

# Instructions
- Carefully read the research theme described in "Research Objective" and understand the problems this research should address, as well as the broader impact it aims to achieve.
- "Hypothesis Info" contains a newly proposed research hypothesis related to the "Research Objective." Read the hypothesis thoroughly and refine it so that it becomes a research contribution with stronger novelty and significance.
- The reasoning behind the evaluation of novelty is provided in "Novelty," and the reasoning for significance is provided in "Significance." Use these evaluations as references to improve the research hypothesis.
- "Research Study List" provides a set of related prior studies. Each entry includes a summary of its title, main contributions, methodologies, results, and limitations. Read through these summaries to understand the direction and focus of research in this domain.
- "Hypothesis Info History" contains past research hypotheses and their evaluation reasoning. If provided, use it as a reference for refining the current hypothesis.
- Pay close attention to how each prior study builds upon earlier work and which limitations remain unresolved. Organize this information to form a clear understanding of the current research landscape.
- Identify the key gaps, challenges, or unmet needs that persist across these studies. Also, consider whether methods or concepts from other domains could help address these limitations.
- Reflect on unexplored aspects or areas for improvement (e.g., new techniques, new evaluation metrics, novel datasets, or methods for generalizing findings). Ensure that the refined hypothesis is broadly applicable and not overly dependent on a specific dataset or model.
- Please limit research hypotheses to those that can be validated with a Python script.
- Please also consider ways to enhance the feasibility of validation and improve accordingly.

# Research Objective
{{ research_objective }}

# Current Hypothesis
{{ current_hypothesis }}

# Novelty
{{ novelty_reason }}

# Significance
{{ significance_reason }}

# Hypothesis History
{{ evaluated_hypothesis_history }}

# Research Study List
{{ research_study_list }}

# Output content:
Based on the above analysis, refine the current hypothesis to make it more novel and significant. Your output should include:

- open_problems
    - Identify the key limitation or gap that the refined hypothesis addresses.
    - Ensure this problem is more focused and impactful than the current hypothesis.

- method
    - Describe the refined approach with improved clarity and detail.
    - Highlight what makes this method novel compared to existing work.

- experimental_setup
    - Provide a concrete and feasible experimental design.
    - Specify which datasets and evaluation metrics will be used.
    - Design clear comparisons with baseline methods.

- primary_metric
    - Specify the single most important evaluation metric that will be used to assess the effectiveness of the proposed method.
    - This metric will be used for calculating the performance gap (GAP) between the proposed method and baselines.
    - Choose a metric that best represents the success of addressing the identified problem (e.g., "accuracy", "f1_score", "bleu", "perplexity").
    - Use a clear, standard metric name that can be directly extracted from experimental results.

- experimental_code
    - Output the core Python code implementing the refined method.
    - Focus on the key improvements and changes.
    - Keep the code concise, readable, and executable.

- expected_result
    - Describe the expected experimental results and performance improvement over baseline methods.
    - Include specific quantitative predictions for the primary metric and other key evaluation metrics.
    - These predictions help determine whether higher or lower metric values indicate better performance.

- expected_conclusion
    - Summarize the academic and practical value of the refined hypothesis.
    - Explain why this hypothesis is more novel and significant than the current version."""
