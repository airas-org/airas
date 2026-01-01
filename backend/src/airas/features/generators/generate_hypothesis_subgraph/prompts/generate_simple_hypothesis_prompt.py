generate_simple_hypothesis_prompt = """\
You are a researcher in machine learning. Based on the instructions below, please generate a simple new research method with minimal modifications to existing approaches.

# Instructions:
- Read the research objective described below:
    {{ research_objective }}
- A list of related prior studies is provided. Each entry contains a summary of its title, main contributions, methodologies, results, and limitations:
    {{ research_study_list }}
- Identify the most promising existing method that can be improved with minimal modifications to its objective function or core algorithm.
- Propose a new method that requires only small, focused changes to the existing approach (e.g., adding a regularization term, modifying the loss function, or introducing a simple weighting mechanism).
- Ensure the proposed method can be validated with a simple Python experiment.

# Output content:
Based on the above analysis, propose a simple new research method that advances the field through minimal but effective modifications. Your output should include:

- open_problems
    - Identify the key limitation in existing methods that can be addressed with minimal modifications.
    - Focus on problems that can be solved through simple changes to objective functions or algorithms.

- method
    - Describe the minimal modification to the existing method (e.g., adding regularization, modifying loss function).
    - Explain the theoretical motivation for this change.
    - Keep the modification simple and focused on the identified problem.

- experimental_setup
    - Provide a concrete but simple experimental design.
    - Specify which datasets and evaluation metrics will be used.
    - Design a straightforward comparison with the base method.

- primary_metric
    - Specify the single most important evaluation metric that will be used to assess the effectiveness of the proposed method.
    - This metric will be used for calculating the performance gap (GAP) between the proposed method and baselines.
    - Choose a metric that best represents the success of addressing the identified problem (e.g., "accuracy", "f1_score", "bleu", "perplexity").
    - Use a clear, standard metric name that can be directly extracted from experimental results.
    - Do NOT include explanations or additional descriptions here. Save those for expected_result.

- experimental_code
    - Output the core Python code implementing the proposed modification.
    - Focus only on the key changes to the base method.
    - Keep the code concise and readable.

- expected_result
    - Describe the expected experimental results and performance improvement over the base method.
    - Include specific quantitative predictions for the primary metric and other key evaluation metrics.
    - These predictions help determine whether higher or lower metric values indicate better performance.

- expected_conclusion
    - Summarize the practical value of the minimal modification.
    - Explain why this simple change leads to meaningful improvement."""
