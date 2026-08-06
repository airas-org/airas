generate_simple_hypothesis_prompt = """\
You are a researcher. Based on the instructions below, please generate a simple new research proposal that advances prior work through a minimal modification.

# Instructions:
- Read the research objective described below:
    {{ research_topic }}
- A list of related prior studies is provided. Each entry contains a summary of its title, main contributions, methodologies, results, and limitations:
    {{ research_study_list }}
- Identify the most promising existing work that can be improved with a minimal, focused modification.
- Propose a change that requires only small, focused modifications to that prior work.
- Let the research objective decide WHAT KIND of contribution this is. Do NOT assume the contribution must be a change to a model or to how it is trained. A minimal modification may be, for example:
    * a change to a method's objective function or core algorithm (e.g., adding a regularization term, modifying the loss function, or introducing a simple weighting mechanism);
    * a change to an evaluation or aggregation procedure (e.g., scoring or ranking results differently, or reporting stratified results where they were previously pooled);
    * a change to how a dataset or benchmark is constructed, filtered, or split (e.g., a stricter held-out split, a different negative-sampling rule, or an added subset);
    * a change to a system's decision rule or pipeline step (e.g., a different acceptance threshold, a reordering of stages, or an added filtering step).
  These are illustrations, not an exhaustive list. If the research objective calls for a benchmark, an evaluation methodology, a dataset, or a system as the contribution, propose that, not a method modification.
- Whatever its kind, the change must stay small and clearly attributable, so that its effect can be isolated by comparing against the unmodified prior work.
- Ensure the proposal can be validated with a simple Python experiment.

# Output content:
Based on the above analysis, propose a simple new research proposal that advances the field through a minimal but effective modification. Your output should include:

- open_problems
    - Identify the key limitation in existing work that can be addressed with a minimal modification.
    - Focus on problems that can be solved through a simple, well-scoped change, whatever part of the prior work that change touches.

- method
    - Describe the minimal modification to the prior work, and state clearly which part of it the change touches (its algorithm, its evaluation procedure, its data, or its system behavior).
    - Explain the motivation for this change.
    - Keep the modification simple and focused on the identified problem.

- experimental_setup
    - Provide a concrete but simple experimental design.
    - Specify what will be evaluated (datasets, benchmarks, or existing artifacts) and which evaluation metrics will be used.
    - Design a straightforward comparison against the unmodified prior work.

- primary_metric
    - Specify the single most important evaluation metric that will be used to assess the effectiveness of the proposal.
    - This metric will be used for calculating the performance gap (GAP) between the proposal and baselines, so it MUST be exactly one metric name.
    - Choose a metric that best represents the success of addressing the identified problem (e.g., "accuracy", "f1_score", "bleu", "perplexity", "spearman_r", "success_rate").
    - Use a clear, standard metric name that can be directly extracted from experimental results.
    - Do NOT include explanations or additional descriptions here. Save those for expected_result.

- supporting_metrics
    - Optional. A list of additional standard metric names that should be reported alongside the primary metric.
    - Use this when a single number does not capture the claim (for example, when the point of the research is that the primary metric alone is insufficient, or when performance must be read across several axes).
    - Each entry must follow the same rules as primary_metric: one clear, standard, directly extractable name, with no explanation attached.
    - These metrics are REPORTED separately; they are NOT aggregated into the primary metric and are NOT used for the GAP calculation. Do not repeat the primary metric here.
    - Leave this list empty if the primary metric alone is sufficient.

- experimental_code
    - Optional. A short Python sketch that illustrates the idea, e.g. the key change expressed as a few lines.
    - This is an ILLUSTRATION, NOT the implementation. The actual experiment is implemented later against a real repository, data, and code template that you have not seen, and this sketch will be rewritten. Do not attempt a runnable or complete program.
    - Leave this field empty if you cannot write a sketch that faithfully reflects the proposed change.

- expected_result
    - Describe the expected experimental results and the improvement over the unmodified prior work.
    - Include specific quantitative predictions for the primary metric and for any supporting metrics.
    - These predictions help determine whether higher or lower metric values indicate better performance.

- expected_conclusion
    - Summarize the practical value of the minimal modification.
    - Explain why this simple change leads to a meaningful improvement."""
