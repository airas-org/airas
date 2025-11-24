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
{{ research_study_list }}"""
