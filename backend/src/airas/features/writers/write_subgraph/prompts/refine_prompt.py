refine_prompt = """\
You are refining an existing research paper to improve its quality, clarity, and academic rigor.

# Current Paper Content
{{ content }}

# Refinement Instructions
- Maintain all the original requirements and guidelines from the system instructions.
- Improve the writing quality, flow, and clarity while preserving all technical content.
- Ensure proper citation placement and format throughout the paper.
    - All citations must use Pandoc/Quarto format: [@citation_key]
    - Examples: [@vaswani-2017-attention], [@devlin-2018-bert; @brown-2020-language]
    - Do NOT use other formats like [citation_key] or \\cite{key}
    - Only cite papers that are contextually relevant; you do NOT need to cite all papers from Reference Candidates
- Verify that all figures are properly referenced and captioned.
- Check for and fix any grammatical, spelling, or formatting errors.
- Enhance the academic tone and structure where needed.
- If there are four or more subsections within a section, please connect the text into a coherent and well-structured narrative.
- Ensure all sections have substantial content appropriate for an 8-page paper."""
