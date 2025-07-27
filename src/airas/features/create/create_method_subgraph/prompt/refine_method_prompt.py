refine_method_prompt = """\
You are a creative AI researcher. Based on the instructions below, please refine the new research idea provided.
# Instructions:
- Carefully read the research theme described below and any additional objectives or constraints. Understand what problem the research should address and the broader impact we want to achieve.
  {{ research_topic }}
- The following is a new research idea that builds on the previous studies and addresses the identified gaps. Please refine this research idea.
  {{ new_idea }}
- A list of prior studies is provided, each summarised by its title, main contributions, methodologies, results and limitations. Read these summaries to understand the evolution of research in this area. The following are previous studies. Please ensure that your research is clearly novel compared to these studies.
  {{ research_study_list }}
- The following are ideas that have been considered in previous studies. Please make sure your idea is different from these.
  {{ idea_history }}
- Output content
   - Based on the above analysis, outline a new research idea that meaningfully advances the field. Provide the following:
     - **Motivation:** Explain why this idea matters, linking it to identified gaps and trends.
     - **Methodology:** Describe the high-level approach, including what new components, functions or changes would be added to an existing system or codebase and what data or algorithms are needed. Indicate how this differs from prior work.
     - **Expected impact:** Articulate the anticipated benefits or potential applications."""
