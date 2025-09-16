generate_ide_and_research_summary_prompt = """\
You are an accomplished researcher in machine learning. Based on the instructions below, please generate a new research idea.
# Instructions:
- Carefully read the research topic described below and understand the problems this research should address as well as the broader impact it aims to achieve.
    {{ research_topic }}
- A list of related prior studies is provided. Each entry contains a summary of its title, main contributions, methodologies, results, and limitations. Read through these summaries to understand the direction and focus of research in this field.
    {{ research_study_list }}
- Pay attention to how each study builds upon previous work and which limitations remain unresolved. Organize this information to form a clear picture of the current research landscape.
- Identify significant gaps, challenges, or unmet needs that persist across these studies. Consider whether there are opportunities to apply methods or concepts from other domains to overcome these limitations.
- Reflect on aspects that have not yet been explored or could be improved (e.g., new techniques, new evaluation metrics, novel datasets, or approaches to generalizing findings). Ensure that your idea is broadly applicable and not overly dependent on a specific dataset or model.
- Please limit research ideas to those that can be validated with a Python script.
- Output content:
    Based on the above analysis, propose a new research idea that meaningfully advances the field. Your output should include:
    - open_problems
        - Select one key challenge in the target research area and provide a detailed summary of it.
        - Choose a problem whose resolution would have a significant impact.
    - methods
        - Provide a detailed description of the approach for solving the identified problem.
        - Describe a high-level strategy, specifying what new components, features, or modifications should be added to existing systems or codebases, what data or algorithms are needed, and how this differs from prior work.
    - experimental_setup
        - Provide a concrete description of the experiments to demonstrate the effectiveness of the proposed method.
        - Specify which models and datasets will be used, the evaluation metrics for quantitative assessment, and how comparisons will be made with baseline methods.
        - Design experiments to evaluate robustness from multiple perspectives.
    - result
        - Describe the expected experimental results based on the "experimental_setup."
    - conclusion
        - Summarize the academic and practical value of the new method based on the experimental results.
        - Discuss its potential for future development."""
