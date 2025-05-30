from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.utils.api_client.llm_facade_client import LLM_MODEL, LLMFacadeClient

logger = getLogger(__name__)

env = Environment()


class PaperContent(BaseModel):
    Title: str
    Abstract: str
    Introduction: str
    Related_Work: str
    Background: str
    Method: str
    Experimental_Setup: str
    Results: str
    Conclusions: str


class WritingNode:
    def __init__(
        self,
        llm_name: LLM_MODEL,
        refine_round: int = 2,
        refine_only: bool = False,
        target_sections: list[str] | None = None,
        client: LLMFacadeClient | None = None, 
    ):
        if target_sections is None:
            target_sections = []

        self.llm_name = llm_name
        self.client = client
        if self.client is None:
            self.client = LLMFacadeClient(llm_name=self.llm_name)

        self.refine_round = refine_round
        self.refine_only = refine_only
        self.target_sections = target_sections or [
            "Title",
            "Abstract",
            "Introduction",
            "Related Work",
            "Background",
            "Method",
            "Experimental Setup",
            "Results",
            "Conclusions",
        ]
        self.per_section_tips_prompt_dict = {
            "Title": """\n
- Write only the title of the paper in one single line, as plain text with no quotation marks.
    - Example of correct output: Efficient Adaptation of Large Language Models via Low-Rank Optimization
    - Incorrect output: "Efficient Adaptation of Large Language Models via Low-Rank Optimization"
- The title must be concise and descriptive of the paper's concept, but try by creative with it.
- Do not include any explanations, subsections""",
            "Abstract": """\n
- Expected length: about 1000 characters
- TL;DR of the paper
- What are we trying to do and why is it relevant?
- Why is this hard? 
- How do we solve it (i.e. our contribution!)
- How do we verify that we solved it (e.g. Experiments and results)
- Avoid using itemize, subheadings, or displayed equations in the abstract; keep math in plain text and list contributions inline.
- Please make sure the abstract reads smoothly and is well-motivated. This should be one continuous paragraph with no breaks between the lines.""",
            "Introduction": """\n
- Expected length: about 4000 characters (~1–1.5 pages)
- Longer version of the Abstract, i.e. of the entire paper
- What are we trying to do and why is it relevant?
- Why is this hard? 
- How do we solve it (i.e. our contribution!)
- How do we verify that we solved it (e.g. Experiments and results)
- New trend: specifically list your contributions as bullet points
- Extra space? Future work!""",
            "Related Work": """\n
- Expected length: about 3000 characters (~1 pages)
- Academic siblings of our work, i.e. alternative attempts in literature at trying to solve the same problem. 
- Goal is to “Compare and contrast” - how does their approach differ in either assumptions or method? If their method is applicable to our Problem Setting I expect a comparison in the experimental section. If not, there needs to be a clear statement why a given method is not applicable. 
- Note: Just describing what another paper is doing is not enough. We need to compare and contrast.""",
            "Background": """\n
- Expected length: about 3000 characters (~1 pages)
- Academic Ancestors of our work, i.e. all concepts and prior work that are required for understanding our method. 
- Usually includes a subsection, Problem Setting, which formally introduces the problem setting and notation (Formalism) for our method. Highlights any specific assumptions that are made that are unusual. 
- Note: If our paper introduces a novel problem setting as part of its contributions, it's best to have a separate Section.""",
            "Method": """\n
- Expected length: about 4000 characters (~1–1.5 pages)
- What we do. Why we do it. All described using the general Formalism introduced in the Problem Setting and building on top of the concepts / foundations introduced in Background.""",
            "Experimental Setup": """
- Expected length: about 4000 characters (~1–1.5 pages)
- How do we test that our stuff works? Introduces a specific instantiation of the Problem Setting and specific implementation details of our Method for this Problem Setting.
- Do not imagine unknown hardware details.
- Includes a description of the dataset, evaluation metrics, important hyperparameters, and implementation details.""",
            "Results": """\n
- Expected length: about 4000 characters (~1–1.5 pages)
- Shows the results of running Method on our problem described in Experimental Setup.
- Includes statements on hyperparameters and other potential issues of fairness.
- Only includes results that have actually been run and saved in the logs. Do not hallucinate results that don't exist.
- If results exist: compares to baselines and includes statistics and confidence intervals. 
- If results exist: includes ablation studies to show that specific parts of the method are relevant.
- Discusses limitations of the method.
- Make sure to include all the results from the experiments, and include all relevant figures.""",
            "Conclusions": """\n
- Expected length: about 2000 characters (~0.5 pages)
- Brief recap of the entire paper.
- To keep going with the analogy, you can think of future work as (potential) academic offspring.""",
        }

        self.system_prompt = """\n
Your goal is to write a clear, structured, and academically rigorous research paper in plain English.
Avoid LaTeX commands or special formatting; focus solely on academic content quality.

The paper should contain the following sections and some tips are provided below:
{% for section, tips in tips_dict.items() %}
## {{ section }} Tips
{{ tips }}
{% endfor %}

Here is the context of the entire paper:
{{ note }}

**Instructions**:
- Use ONLY the information provided in the context above. 
    - DO NOT add any assumptions, invented data, or details that are not explicitly mentioned in the context.

- Ensure that ALL relevant details from the context are included.
    - You must include **all figures provided in the context**, regardless of perceived relevance. Do not omit any.
    - You are free to organize and structure the content in a natural and logical way, rather than directly following the order or format of the context.
    - You must include all relevant details of methods, experiments, and results—including mathematical equations, pseudocode (if applicable), experimental setups, configurations, numerical results, and figures/tables.
    - When beneficial for clarity, describe the mathematical equations, parameter settings, and procedures in a structured and easy-to-follow way, using natural language or numbered steps.
    - Avoid overly explanatory or repetitive descriptions that would be self-evident to readers familiar with standard machine learning notation.
    - Keep the experimental results (figures and tables) only in the `Results section`, and make sure that any captions are filled in. 
    - If image filenames (e.g., `figure1.pdf`) are provided in the context, refer to them explicitly in the text.
    - Do not invent or assume the existence of any figures or visual content. If no figure is provided, you must not fabricate or imply the existence of one.

- When referring to figures in the "Results" section:
    - Include a **caption with a descriptive title** (not just the filename).
    - **The caption must start with "Figure N: "** where N is the sequential figure number (e.g., `Figure 1: Convergence comparison ...`).
    - Reference figures in the body text using these numbers (e.g., "As shown in Figure 2...").

- Avoid editor instructions, placeholders, speculative text, or comments like "details are missing."
    - Example: Remove phrases like "Here’s a refined version of this section," as they are not part of the final document.
    - These phrases are found at the beginning of sections, introducing edits or refinements. Carefully review the start of each section for such instructions and ensure they are eliminated while preserving the actual content.

- The full paper should be **about 8 pages long**, meaning **each section should contain substantial content**.

**Output Format Example** (as JSON):
```json
{
  "Title": "Efficient Adaptation of Large Language Models via Low-Rank Optimization",
  "Abstract": "This paper proposes a novel method...",
  "Introduction": "In recent years...",
  "Related_Work": "...",
  "Background": "...",
  "Method": "...",
  "Experimental_Setup": "...",
  "Results": "...",
  "Conclusions": "We conclude that..."
}
```"""

        self.write_prompt_template = """\n
You are writing a research paper."""

        self.refinement_template = """\n
You are refining a research paper.

Here is the content that needs refinement:
{{ content }}

Pay particular attention to fixing any errors such as:
{{ error_list_prompt }}"""

        self.error_list_prompt = """\n
- Unenclosed math symbols
- Grammatical or spelling errors
- Numerical results that do not come from explicit experiments and logs
- Unnecessary verbosity or repetition, unclear text
- Results or insights in the context that have not yet need included
- Any relevant figures that have not yet been included in the text"""

    def _replace_underscores_in_keys(
        self, paper_dict: dict[str, str]
    ) -> dict[str, str]:
        return {key.replace("_", " "): value for key, value in paper_dict.items()}

    def _call_llm(self, prompt: str, system_prompt: str) -> dict[str, str]:
        messages = system_prompt + prompt
        output, cost = self.client.structured_outputs(
            message=messages, data_model=PaperContent
        )
        if output is None:
            raise ValueError("Error: No response from LLM.")

        missing_fields = [
            field
            for field in PaperContent.model_fields
            if field not in output or not output[field].strip()
        ]
        if missing_fields:
            raise ValueError(
                f"Missing or empty fields in model response: {missing_fields}"
            )

        return self._replace_underscores_in_keys(output)

    def _write(self, note: str) -> dict[str, str]:
        prompt = self._generate_write_prompt()
        system_prompt = self._render_system_prompt(note)
        content = self._call_llm(prompt=prompt, system_prompt=system_prompt)
        if not content:
            raise RuntimeError("Failed to generate content. The LLM returned None.")
        return content

    def _refine(self, note: str, content: dict[str, str]) -> dict[str, str]:
        for round_num in range(self.refine_round):
            prompt = self._generate_refinement_prompt(content)
            system_prompt = self._render_system_prompt(note)
            refine_content = self._call_llm(prompt=prompt, system_prompt=system_prompt)
            if not refine_content:
                logger.warning(
                    f"Refinement failed at round {round_num + 1}. Keeping previous content."
                )
                return content
        return refine_content

    def _render_system_prompt(self, note: str) -> str:
        template = env.from_string(self.system_prompt)
        return template.render(
            note=note,
            tips_dict={
                s: self.per_section_tips_prompt_dict[s] for s in self.target_sections
            },
        )

    def _generate_write_prompt(self) -> str:
        """
        Generate a write prompt for a specific section using Jinja2.
        """
        template = env.from_string(self.write_prompt_template)
        return template.render()

    def _generate_refinement_prompt(self, content: dict[str, str]) -> str:
        """
        Generate a refinement prompt for a specific section using Jinja2.
        """
        template = env.from_string(self.refinement_template)
        return template.render(
            content=content,
            error_list_prompt=self.error_list_prompt,
        )

    def execute(
        self, note: str, paper_content: dict[str, str] | None = None
    ) -> dict[str, str]:
        if not self.refine_only:
            logger.info("Generating full paper in one LLM call...")
            initial_content = self._write(note)
            paper_content = self._refine(note, initial_content)
        else:
            if paper_content is None:
                raise ValueError(
                    "paper_content must be provided when refine_only is True."
                )
            paper_content = self._refine(note, paper_content)
        return paper_content


# related_work_prompt = f"""Please fill in the Related Work of the writeup. Some tips are provided below:
# {per_section_tips["Related Work"]}
# For this section, very briefly sketch out the structure of the section, and clearly indicate what papers you intend to include.
# Do this all in LaTeX comments using %.
# The related work should be concise, only plan to discuss the most relevant work.
# Do not modify `references.bib` to add any new citations, this will be filled in at a later stage.
# Be sure to first name the file and use *SEARCH/REPLACE* blocks to perform these edits."""

# citation_system_msg = """You are an ambitious AI PhD student who is looking to publish a paper that will contribute significantly to the field.
# You have already written an initial draft of the paper and now you are looking to add missing citations to related papers throughout the paper.
# The related work section already has some initial comments on which papers to add and discuss.
# Focus on completing the existing write-up and do not add entirely new elements unless necessary.
# Ensure every point in the paper is substantiated with sufficient evidence.
# Feel free to add more cites to a particular point if there is only one or two references.
# Ensure no paper is cited without a corresponding reference in the `references.bib` file.
# Ensure each paragraph of the related work has sufficient background, e.g. a few papers cited.
# You will be given access to the Semantic Scholar API, only add citations that you have found using the API.
# Aim to discuss a broad range of relevant papers, not just the most popular ones.
# Make sure not to copy verbatim from prior literature to avoid plagiarism.
# You will be prompted to give a precise description of where and how to add the cite, and a search query for the paper to be cited.
# Finally, you will select the most relevant cite from the search results (top 10 results will be shown).
# You will have {total_rounds} rounds to add to the references, but do not need to use them all.
# DO NOT ADD A CITATION THAT ALREADY EXISTS!"""

# citation_first_prompt = '''Round {current_round}/{total_rounds}:
# You have written this LaTeX draft so far:
# """
# {draft}
# """
# Identify the most important citation that you still need to add, and the query to find the paper.
# Respond in the following format:
# THOUGHT:
# <THOUGHT>
# RESPONSE:
# ```json
# <JSON>
# ```
# In <THOUGHT>, first briefly reason over the paper and identify where citations should be added.
# If no more citations are needed, add "No more citations needed" to your thoughts.
# Do not add "No more citations needed" if you are adding citations this round.
# In <JSON>, respond in JSON format with the following fields:
# - "Description": A precise description of the required edit, along with the proposed text and location where it should be made.
# - "Query": The search query to find the paper (e.g. attention is all you need).
# Ensure the description is sufficient to make the change without further context. Someone else will make the change.
# The query will work best if you are able to recall the exact name of the paper you are looking for, or the authors.
# This JSON will be automatically parsed, so ensure the format is precise.'''

# citation_second_prompt = """Search has recovered the following articles:
# {papers}
# Respond in the following format:
# THOUGHT:
# <THOUGHT>
# RESPONSE:
# ```json
# <JSON>
# ```
# In <THOUGHT>, first briefly reason over the search results and identify which citation best fits your paper and the location is to be added at.
# If none are appropriate, add "Do not add any" to your thoughts.
# In <JSON>, respond in JSON format with the following fields:
# - "Selected": A list of the indices of the selected papers to be cited, e.g. "[0, 1]". Can be "[]" if no papers are selected. This must be a string.
# - "Description": Update the previous description of the required edit if needed. Ensure that any cites precisely match the name in the bibtex!!!
# Do not select papers that are already in the `references.bib` file at the top of the draft, or if the same citation exists under a different name.
# This JSON will be automatically parsed, so ensure the format is precise."""
