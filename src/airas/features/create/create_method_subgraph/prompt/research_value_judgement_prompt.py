research_value_judgement_prompt = """\
You are a creative AI researcher. Please use the following guidelines to determine whether a new research idea is valuable.
# Instructions:
- Carefully read the research theme described below and any additional objectives or constraints. Understand what problem the research should address and the broader impact we want to achieve.
  {{ research_topic }}
- The following is a new research idea that builds on the previous studies and addresses the identified gaps. Please evaluate whether this research idea is valuable.
  {{ new_idea }}
- A list of prior studies is provided, each summarised by its title, main contributions, methodologies, results and limitations. Read these summaries to understand the evolution of research in this area. The following are previous studies. Please ensure that your research is clearly novel compared to these studies.
  {{ research_study_list }}
- Output content
  - **reason:** Explain the rationale behind your evaluation, considering the research theme, the new idea, and the prior studies.
  - **judgement_result:** Provide a clear judgement on whether the new research idea is valuable, based on the evidence presented."""
