import os
import re
import subprocess
import shutil
import tempfile
from pydantic import BaseModel
from airas.utils.api_client.llm_facade_client import LLMFacadeClient, LLM_MODEL
from logging import getLogger

logger = getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class LLMOutput(BaseModel):
    latex_full_text: str


class LatexNode:
    def __init__(
        self,
        llm_name: LLM_MODEL,
        figures_dir: str,
        pdf_file_path: str,
        save_dir: str,
        timeout: int = 30,
        latex_template_file_path: str = "latex_subgraph/latex/template.tex",
    ):
        self.llm_name = llm_name
        self.latex_template_file_path = latex_template_file_path
        self.figures_dir = figures_dir
        self.pdf_file_path = pdf_file_path
        self.save_dir = save_dir
        self.timeout = timeout
        self.template_dir = os.path.join(SCRIPT_DIR, "..", "latex")
        self.template_dir = os.path.abspath(self.template_dir)

        self.latex_save_dir = os.path.join(self.save_dir, "latex")
        os.makedirs(self.latex_save_dir, exist_ok=True)
        self.template_copy_file = os.path.join(self.latex_save_dir, "template.tex")
        self.client = LLMFacadeClient(self.llm_name)

    def _call_llm(self, prompt: str) -> str:
        system_prompt = """
You are a helpful LaTeX rewriting assistant.
The value of \"latex_full_text\" must contain the complete LaTeX text."""
        messages = system_prompt + prompt
        output, cost = self.client.structured_outputs(
            message=messages,
            data_model=LLMOutput,
        )
        if output is None:
            raise ValueError("No response")
        if not isinstance(output, dict) or not output:
            raise ValueError("Empty LaTeX content")
        if "latex_full_text" in output:
            if not output["latex_full_text"]:
                raise ValueError("Empty LaTeX content")
            return output["latex_full_text"]
        else:
            raise ValueError("Error: No response from LLM in _call_llm.")

    def _copy_template(self):
        try:
            shutil.copytree(self.template_dir, self.latex_save_dir, dirs_exist_ok=True)
        except Exception as e:
            raise RuntimeError(
                f"Failed to copy directory {self.template_dir} to {self.latex_save_dir}: {e}"
            )

    def _fill_template(self, content: dict) -> str:
        # Read the copied template, replace placeholders with content, and save the updated file
        tex_text = ""
        with open(self.template_copy_file, "r") as f:
            tex_text = f.read()

        for section, value in content.items():
            placeholder = f"{section.upper()} HERE"
            if placeholder in tex_text:
                tex_text = tex_text.replace(placeholder, value)
                logger.info(f"置換完了: {placeholder}")
            else:
                logger.info(f"プレースホルダーが見つかりませんでした: {placeholder}")

        with open(self.template_copy_file, "w") as f:
            f.write(tex_text)
        return tex_text

    def _check_references(self, tex_text: str) -> str:
        # Check for missing references in the LaTeX content against the references.bib section
        cites = re.findall(r"\\cite[a-z]*{([^}]*)}", tex_text)
        bib_path = os.path.join(self.latex_save_dir, "references.bib")
        if not os.path.exists(bib_path):
            raise FileNotFoundError(f"references.bib file is missing at: {bib_path}")

        with open(bib_path, "r") as f:
            bib_text = f.read()
        missing_cites = [cite for cite in cites if cite.strip() not in bib_text]

        if not missing_cites:
            logger.info("No missing references found.")
            return tex_text

        logger.info(f"Missing references found: {missing_cites}")
        prompt = f""""\n
# LaTeX text
--------
{tex_text}
--------
# References.bib content
--------
{bib_text}
--------
The following reference is missing from references.bib: {missing_cites}.
Only modify the BibTeX content or add missing \\cite{{...}} commands if needed.

Do not remove, replace, or summarize any section of the LaTeX text such as Introduction, Method, or Results.
Do not comment out or rewrite any parts. Just fix the missing references.
Return the complete LaTeX document, including any bibtex changes."""
        llm_response = self._call_llm(prompt)
        if llm_response is None:
            raise RuntimeError(
                f"LLM failed to respond for missing references: {missing_cites}"
            )
        return llm_response

    def _check_figures(
        self,
        tex_text: str,
        pattern: str = r"\\includegraphics.*?{(.*?)}",
    ) -> str:
        # Verify all referenced figures in the LaTeX content exist in the figures directory
        all_figs = [f for f in os.listdir(self.figures_dir) if f.endswith(".pdf")]
        if not all_figs:
            logger.info("論文生成に使える図がありません")
            return tex_text

        referenced_figs = re.findall(pattern, tex_text)
        fig_to_use = [fig for fig in referenced_figs if fig in all_figs]
        if not fig_to_use:
            logger.info("論文内で利用している図はありません")
            return tex_text

        prompt = f"""\n
# LaTeX Text
--------
{tex_text}
--------
# Available Images
--------
{fig_to_use}
--------
Please modify and output the above Latex text based on the following instructions.
- Only “Available Images” are available. 
- If a figure is mentioned on Latex Text, please rewrite the content of Latex Text to cite it.
- Do not use diagrams that do not exist in “Available Images”.
- Return the complete LaTeX text."""
        llm_response = self._call_llm(prompt)
        if llm_response is None:
            raise RuntimeError("LLM failed to respond for missing figures")
        return llm_response

    def _check_duplicates(self, tex_text: str, patterns: dict) -> str:
        # Detect and prompt for duplicate elements in the LaTeX content
        for element_type, pattern in patterns.items():
            items = re.findall(pattern, tex_text)
            duplicates = {x for x in items if items.count(x) > 1}
            if duplicates:
                logger.info(f"Duplicate {element_type} found: {duplicates}.")
                prompt = f"""\n
# LaTeX text
--------
{tex_text}
--------
Duplicate {element_type} found: {', '.join(duplicates)}. Ensure any {element_type} is only included once. 
If duplicated, identify the best location for the {element_type} and remove any other.
Return the complete corrected LaTeX text with the duplicates fixed."""
                llm_response = self._call_llm(prompt)
                if llm_response is None:
                    raise RuntimeError(
                        f"LLM failed to respond for missing figures: {duplicates}"
                    )
                tex_text = llm_response
        return tex_text

    def _fix_latex_errors(self, tex_text: str) -> str:
        # Fix LaTeX errors iteratively using chktex and automated suggestions
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".tex", delete=True
            ) as tmp_file:
                tmp_file.write(tex_text)
                tmp_file.flush()

                ignored_warnings = "-n2 -n24 -n13 -n1 -n8 -n29 -n36 -n44"
                check_cmd = f"chktex {tmp_file.name} -q {ignored_warnings}"
                check_output = os.popen(check_cmd).read()

                if check_output:
                    error_messages = check_output.strip().split("\n")
                    formatted_errors = "\n".join(
                        f"- {msg}" for msg in error_messages if msg
                    )
                    logger.info(f"LaTeX エラー検出: {formatted_errors}")

                    prompt = f"""\n
# LaTeX text
--------
{tex_text}
--------
Please fix the following LaTeX errors: {formatted_errors}.      
Make the minimal fix required and do not remove or change any packages unnecessarily.
Pay attention to any accidental uses of HTML syntax, e.g. </end instead of \\end.

Return the complete corrected LaTeX text."""
                    llm_response = self._call_llm(prompt)
                    if llm_response is None:
                        raise RuntimeError("LLM failed to fix LaTeX errors")
                    return llm_response
                else:
                    logger.error("No LaTex errors found by chktex.")
                    return tex_text
        except FileNotFoundError:
            logger.error("chktex command not found. Skipping LaTeX checks.")
            return tex_text

    def _compile_latex(self, cwd: str):
        # Compile the LaTeX document to PDF using pdflatex and bibtex commands
        logger.info("GENERATING LATEX")
        commands = [
            ["pdflatex", "-interaction=nonstopmode", self.template_copy_file],
            ["bibtex", os.path.splitext(self.template_copy_file)[0]],
            ["pdflatex", "-interaction=nonstopmode", self.template_copy_file],
            ["pdflatex", "-interaction=nonstopmode", self.template_copy_file],
        ]

        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=self.timeout,
                    check=True,
                )
                logger.info(f"Standard Output:\n{result.stdout}")
                logger.info(f"Standard Error:\n{result.stderr}")
            except subprocess.TimeoutExpired as e:
                logger.error(f"Latex command timed out: {e}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error running command {' '.join(command)}: {e}")
            except FileNotFoundError:
                logger.error(
                    f"Command not found: {' '.join(command)}. "
                    "Make sure pdflatex and bibtex are installed and on your PATH."
                )
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")

        logger.info("FINISHED GENERATING LATEX")
        pdf_filename = (
            f"{os.path.splitext(os.path.basename(self.template_copy_file))[0]}.pdf"
        )
        try:
            shutil.move(os.path.join(cwd, pdf_filename), self.pdf_file_path)
        except FileNotFoundError:
            logger.info("Failed to rename PDF.")

    def execute(self, paper_tex_content: dict[str, str]) -> str:
        """
        Main entry point:
        1. Copy template
        2. Fill placeholders
        3. Iterate checks (refs, figures, duplicates, minimal error fix)
        4. Compile
        """
        self._copy_template()
        tex_text = self._fill_template(paper_tex_content)
        max_iterations = 10
        iteration_count = 0

        while iteration_count < max_iterations:
            logger.info(f"Start iteration: {iteration_count}")

            # logger.info("Check references...")
            # original_tex_text = tex_text
            # tex_text = self._check_references(tex_text)
            # if tex_text != original_tex_text:
            #     iteration_count += 1
            #     continue

            logger.info("Check figures...")
            original_tex_text = tex_text
            tex_text = self._check_figures(tex_text)
            if tex_text != original_tex_text:
                iteration_count += 1
                continue

            logger.info("Check duplicates...")
            original_tex_text = tex_text
            tex_text = self._check_duplicates(
                tex_text,
                {
                    "figure": r"\\includegraphics.*?{(.*?)}",
                    "section header": r"\\section{([^}]*)}",
                },
            )
            if tex_text != original_tex_text:
                iteration_count += 1
                continue

            logger.info("Check LaTeX errors...")
            original_tex_text = tex_text
            tex_text = self._fix_latex_errors(tex_text)
            if tex_text != original_tex_text:
                iteration_count += 1
                continue

            logger.info("No changes detected, exiting loop.")
            break

        if iteration_count == max_iterations:
            logger.info(f"Maximum iterations reached ({max_iterations}), exiting loop.")

        with open(self.template_copy_file, "w") as f:
            f.write(tex_text)

        try:
            self._compile_latex(os.path.dirname(self.template_copy_file))
            return tex_text

        except Exception as e:
            logger.info(f"Error occurred during compiling: {e}")
            return tex_text
