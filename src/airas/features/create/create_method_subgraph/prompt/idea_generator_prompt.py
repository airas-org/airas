idea_generator_prompt = """\
You are a researcher in creative AI.Please generate new ideas based on the following instructions.
# Instructions:
- Carefully read the research theme described below and any additional objectives or constraints. Understand what problem the research should address and the broader impact we want to achieve.
  {{ research_topic }}
- A list of prior studies is provided, each summarised by its title, main contributions, methodologies, results and limitations. Read these summaries to understand the evolution of research in this area. The following are previous studies.
  {{ research_study_list }}
- Pay attention to how each study builds on the previous ones and what limitations remain unresolved. Organise this information in your mind to get a clear picture of the current landscape.
- Identify significant gaps, challenges or unmet needs that persist across these studies. Consider whether there are opportunities to apply methods or concepts from other domains to overcome these limitations.
- Reflect on what has not been explored or what could be improved (e.g., new techniques, new evaluation metrics, novel data or ways to generalise findings). Ensure your idea is not overly tailored to a specific dataset or model but could have broad applicability.
- The following are research ideas that have been considered so far. Please consider ideas that are different from these.
  {{ idea_history }}
- Output content
   - Based on the above analysis, outline a new research idea that meaningfully advances the field. Provide the following:
     - **Motivation:** Explain why this idea matters, linking it to identified gaps and trends.
     - **Methodology:** Describe the high-level approach, including what new components, functions or changes would be added to an existing system or codebase and what data or algorithms are needed. Indicate how this differs from prior work.
     - **Expected impact:** Articulate the anticipated benefits or potential applications."""
