refine_prompt = """\
You are refining an existing research paper to improve its quality, clarity, and academic rigor.

# Current Paper Content
{{ content }}

# Refinement Instructions

- Abstract
  - Clearly separate problem motivation, method, key results, and implications into distinct sentences with minimal overlap.
  - Quantitative results should be framed to emphasize relative improvement or qualitative trend, not just raw numbers.
  - Avoid excessive methodological detail; the abstract should communicate what was done and why it matters, not how every component works.
  - Explicitly state the practical or conceptual contribution in the final sentence.

- Introduction
  - Strengthen the opening by moving from broad problem context → concrete gap → proposed direction more explicitly.
  - Clearly articulate the limitations of existing approaches before introducing the proposed solution.
  - Distinguish between scientific motivation (why the problem is interesting) and practical motivation (why the setting or constraints matter).
  - Ensure that the list of contributions is concise, non-overlapping, and phrased as outcomes, not implementation steps.

- Related Work
  - Organize prior work into clear thematic clusters rather than sequential summaries of individual papers.
  - For each cluster, explicitly state what is missing or insufficient relative to the current work.
  - Reduce descriptive repetition by focusing on comparative positioning rather than restating known benchmarks or datasets.
  - Clarify how the paper’s perspective differs conceptually (e.g., assumptions, constraints, evaluation regime), not only technically.

- Background
  - Use this section to define task assumptions and terminology precisely, not to restate well-known material.
  - Introduce notation and formal definitions only when they are later used in analysis or methodology.
  - Clearly separate task definition, dataset characteristics, and evaluation protocol into subsections or paragraphs.
  - Avoid forward references to proposed methods; background should remain method-agnostic.

- Method
  - Begin with a high-level overview paragraph that explains the method conceptually before introducing stages or components.
  - Ensure that each subsection answers a distinct question (e.g., “what is generated,” “how it is validated,” “why this step exists”).
  - Explicitly link design choices to specific failure modes or challenges identified earlier in the paper.
  - Maintain consistent terminology across stages to reduce cognitive load for the reader.

- Experimental Setup
  - Clearly justify data selection, sampling, and evaluation scope in terms of validity and constraints.
  - Separate what is controlled, what is varied, and what is held constant across experiments.
  - Avoid implementation-heavy details unless they affect reproducibility or interpretation.
  - Make explicit any limitations introduced by experimental design choices.

- Results
  - Structure results presentation around patterns and trends, not individual experiment descriptions.
  - Use consistent phrasing when comparing baseline and proposed methods to improve readability.
  - Explicitly separate observations (what happened) from interpretations (why it may have happened).
  - Avoid overemphasizing best-case results; instead, highlight robustness and consistency across conditions.

- Discussion / Analysis (if separate, or implicit)
  - Connect empirical findings back to the original research questions or hypotheses.
  - Discuss both strengths and failure cases symmetrically to enhance credibility.
  - Clarify which limitations are inherent to the problem setting versus artifacts of the chosen approach.
  - Avoid speculative claims unless they are clearly labeled as hypotheses for future work.

- Conclusion
  - Restate contributions at a conceptual level, not by repeating experimental outcomes verbatim.
  - Clearly distinguish between what has been demonstrated and what remains unresolved.
  - Emphasize the broader implications for the field or application domain.
  - End with forward-looking statements that are specific but non-committal, avoiding promises not supported by results.

- Overall Writing Style and Structure
  - Maintain a consistent level of abstraction within each section.
  - Prefer active voice when describing methodological intent and contributions.
  - Ensure that all claims are either supported by evidence or clearly framed as assumptions.
  - Regularly check that section boundaries align with reader expectations (e.g., no results in Method, no methods in Conclusion).
  - Please do not make any changes whatsoever to the sections where academic papers are cited. Also, do not modify any parts enclosed in [ ].

# Output

Please provide the following items individually:
- title
- abstract
- introduction
- related_work
- background
- method
- experimental_setup
- results
- conclusion"""
