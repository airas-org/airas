generate_simple_hypothesis_prompt = """\
You are a researcher in machine learning. Based on the instructions below, please generate a simple new research method with minimal modifications to existing approaches.

# Instructions:
- Read the research topic described below:
    {{ research_topic }}
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

- methods
    - Describe the minimal modification to the existing method (e.g., adding regularization, modifying loss function).
    - Explain the theoretical motivation for this change.
    - Keep the modification simple and focused on the identified problem.

- experimental_setup
    - Provide a concrete but simple experimental design.
    - Specify which datasets and evaluation metrics will be used.
    - Design a straightforward comparison with the base method.

- experimental_code
    - Output the core Python code implementing the proposed modification.
    - Focus only on the key changes to the base method.
    - Keep the code concise and readable.

- expected_result
    - Describe the expected experimental results and performance improvement over the base method.

- expected_conclusion
    - Summarize the practical value of the minimal modification.
    - Explain why this simple change leads to meaningful improvement."""
