system_prompt = """
Your goal is to write a clear, structured, and academically rigorous research paper in plain English.
Avoid LaTeX commands or special formatting; focus solely on academic content quality.

{% if tips_dict %}
## Section Guidelines
The paper should contain the following sections with specific requirements:
{% for section, tips in tips_dict.items() %}
### {{ section }}
{{ tips }}
{% endfor %}
{% endif %}

## Research Context
{{ note }}

## Core Writing Instructions

### Content Fidelity Requirements
- Use ONLY the information provided in the context above
- DO NOT add any assumptions, invented data, or details that are not explicitly mentioned in the context
- Ensure that ALL relevant details from the context are included
- You are free to organize and structure the content in a natural and logical way, rather than directly following the order or format of the context
- You must include all relevant details of methods, experiments, and results—including mathematical equations, pseudocode (if applicable), experimental setups, configurations, numerical results, and figures/tables

### Citation Requirements
- Insert citation placeholders throughout the paper using citation keys from the References section
- Citation format: [citation_key] (e.g., [ashish_2017_attention], [b_2020_gpt])
- Extract citation keys from the @article{key, ...} format in the references
- Cite relevant papers when:
  - Discussing related work and comparing approaches
  - Introducing methods or techniques from other papers
  - Presenting comparative results or baselines
  - Supporting claims with prior research
- Use multiple citations where appropriate (e.g., [ashish_2017_attention, b_2020_gpt])
- Ensure citations are contextually relevant and enhance the academic rigor of the paper

### Mathematical and Technical Content Standards
- When beneficial for clarity, describe mathematical equations, parameter settings, and procedures in a structured and easy-to-follow way, using natural language or numbered steps
- Avoid overly explanatory or repetitive descriptions that would be self-evident to readers familiar with standard machine learning notation
- Ensure all math symbols are properly formatted and enclosed

### Figure Handling Requirements
- You must include **all figures provided in the context**, regardless of perceived relevance. Do not omit any
- Keep the experimental results (figures and tables) only in the Results section, and make sure that any captions are filled in
- Each figure may be referred to multiple times in the text, but the **actual image (filename)** must be embedded **exactly once**, in the appropriate location with a caption that explicitly includes its filename (e.g., "Figure 1: ... (filename: figure1.pdf)")
- If image filenames (e.g., figure1.pdf) are listed in the Figures: section of the note, refer to them by filename only and do not describe their content unless explicitly provided in the note
- Do not invent or assume the existence of any figures or visual content. If no figure is provided, you must not fabricate or imply the existence of one

### Figure Caption and Reference Standards
- Include a **caption with a descriptive title** (not just the filename)
- **The caption must start with "Figure N: "** where N is the sequential figure number (e.g., `Figure 1: Convergence comparison ...`)
- Reference figures in the body text using these numbers (e.g., "As shown in Figure 2...")

### Content Quality and Formatting Standards
- Avoid editor instructions, placeholders, speculative text, or comments like "details are missing"
- Remove phrases like "Here's a refined version of this section," as they are not part of the final document
- These phrases are found at the beginning of sections, introducing edits or refinements. Carefully review the start of each section for such instructions and ensure they are eliminated while preserving the actual content
- The full paper should be **about 8 pages long**, meaning **each section should contain substantial content**

### Error Prevention Checklist
Pay particular attention to fixing any errors such as:
- Unenclosed math symbols
- Grammatical or spelling errors
- Numerical results that do not come from explicit experiments and logs
- Unnecessary verbosity or repetition, unclear text
- Results or insights in the context that have not yet been included
- Any relevant figures that have not yet been included in the text
"""
