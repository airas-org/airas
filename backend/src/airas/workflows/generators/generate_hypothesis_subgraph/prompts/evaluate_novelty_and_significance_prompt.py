evaluate_novelty_and_significance_prompt = """\
You are an accomplished researcher in machine learning. You are considering a new hypothesis described in "New Hypothesis" for the research theme provided in "Research Topic". "Related Works" is a list of research papers that are highly relevant to this new hypothesis.
Based on the following instructions, output the reasons for the novelty and significance of the newly proposed hypothesis, and quantitatively evaluate them.

# Research Objective
{{ research_topic }}

# New Hypothesis
{{ new_hypothesis }}

# Related Works
{{ research_study_list }}

# Instructions
Following the instructions below, please provide an evaluation of the new hypothesis.
Since I aim to pursue research of high academic significance, I request that the assessment be conducted with rigorous standards.
- output
    - novelty_reason
        - Determine whether the new hypothesis has novelty, and output the reason.
        - The reason should be as specific as possible.
        - Carefully review the content of the studies provided in "Related Works" before outputting.
    - novelty_score
        - Score the novelty of the new hypothesis on a scale of 1 to 10, where 1 means no novelty at all and 10 means extremely high novelty.
    - significance_reason
        - Determine whether the new hypothesis is significant, and output the reason.
        - Significance includes both academic and societal importance.
    - significance_score
        - Score the significance of the new hypothesis on a scale of 1 to 10, where 1 means no significance at all and 10 means extremely high significance."""
