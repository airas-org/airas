iclr2024_section_tips_prompt = {
    "Title": """\
- Write only the title of the paper in one single line, as plain text with no quotation marks
- Example of correct output: Efficient Adaptation of Large Language Models via Low-Rank Optimization
- Incorrect output: "Efficient Adaptation of Large Language Models via Low-Rank Optimization"
- The title must be concise and descriptive of the paper's concept, but try to be creative with it
- Do not include any explanations or subsections""",
    "Abstract": """\
- Expected length: about 1000 characters
- TL;DR of the paper covering:
    - What are we trying to do and why is it relevant?
    - Why is this hard?
    - How do we solve it (i.e. our contribution!)
    - How do we verify that we solved it (e.g. Experiments and results)
- Avoid using itemize, subheadings, or displayed equations in the abstract; keep math in plain text and list contributions inline
- This should be one continuous paragraph with no breaks between the lines
- Make sure the abstract reads smoothly and is well-motivated""",
    "Introduction": """\
- Expected length: about 4000 characters (~1–1.5 pages)
- Longer version of the Abstract, covering the entire paper scope
- Structure should address:
    - What are we trying to do and why is it relevant?
    - Why is this hard?
    - How do we solve it (i.e. our contribution!)
    - How do we verify that we solved it (e.g. Experiments and results)
- Include citations to establish context and motivate the problem
- New trend: specifically list your contributions as bullet points
- Extra space? Include future work discussion!""",
    "Related Work": """\
- Expected length: about 3000 characters (~1 page)
- Academic siblings of our work, i.e. alternative attempts in literature at trying to solve the same problem
- Goal is to "Compare and contrast" - how does their approach differ in either assumptions or method?
- If their method is applicable to our Problem Setting, expect a comparison in the experimental section
- If not applicable, provide a clear statement why a given method is not applicable
- Note: Just describing what another paper is doing is not enough. We need to compare and contrast
- Include extensive citations to related work with proper contextual discussion""",
    "Background": """\
- Expected length: about 3000 characters (~1 page)
- Academic Ancestors of our work, i.e. all concepts and prior work required for understanding our method
- Usually includes a subsection, Problem Setting, which formally introduces the problem setting and notation (Formalism) for our method
- Highlights any specific assumptions that are made that are unusual
- Include citations to foundational work and key concepts
    - Note: If our paper introduces a novel problem setting as part of its contributions, it's best to have a separate Problem Setting section
    - Please avoid dividing the text into too many subsections, and instead present it as a coherent, well-connected narrative""",
    "Method": """\
- Expected length: about 4000 characters (~1–1.5 pages)
- What we do. Why we do it. All described using the general Formalism introduced in the Problem Setting and building on top of the concepts/foundations introduced in Background
- Include citations only when building upon or adapting existing methods or techniques
- Provide clear technical descriptions with proper mathematical notation
- Please avoid dividing the text into too many subsections, and instead present it as a coherent, well-connected narrative.""",
    "Experimental Setup": """\
- Expected length: about 4000 characters (~1–1.5 pages)
- How do we test that our stuff works? Introduces a specific instantiation of the Problem Setting and specific implementation details of our Method for this Problem Setting
- Do not imagine unknown hardware details
- Includes a description of the dataset, evaluation metrics, important hyperparameters, and implementation details
- Include citations for datasets, established evaluation metrics, and baseline methods used for comparison
- Please avoid dividing the text into too many subsections, and instead present it as a coherent, well-connected narrative.""",
    "Results": """\
- Expected length: about 4000 characters (~1–1.5 pages)
- Shows the results of running Method on our problem described in Experimental Setup
- Includes statements on hyperparameters and other potential issues of fairness
- Only includes results that have actually been run and saved in the logs. Do not hallucinate results that don't exist
- If results exist: compares to baselines and includes statistics and confidence intervals
- If results exist: includes ablation studies to show that specific parts of the method are relevant
- Discusses limitations of the method
- Make sure to include all the results from the experiments, and include all relevant figures
- Include citations only when directly comparing to baseline methods or referencing related experimental results
- Please organize and summarize the results by dividing them into sections for each experiment.""",
    "Conclusion": """\
- Expected length: about 2000 characters (~0.5 pages)
- Brief recap of the entire paper
- Summarize key contributions and their implications
- To keep going with the analogy, you can think of future work as (potential) academic offspring
- Citations are generally not necessary unless discussing specific future research directions""",
}
