# ruff: noqa: E402
from fastmcp import FastMCP

from airas.services.mcp_server.mcp_tools.create_mcp_tool import (
    create_mcp_tool as create_mcp_tool_logic,
)

# Initialize FastMCP server
mcp: FastMCP = FastMCP("airas")


@mcp.tool(
    description="Given a Python module path, this tool reads the source code, generates a corresponding MCP tool using an LLM, saves it to the appropriate directory, and automatically registers it to the MCP server."
)
async def create_mcp_tool(
    module_path: str,
) -> str | None:
    """
    Automatically generate and register an MCP-compatible tool using a language model.

    This tool takes the module path of a Python subgraph implementation, loads its source code,
    sends it to an LLM using a Jinja2 template prompt, and automatically registers a FastMCP-compatible tool into the MCP server.

    Args:
        module_path (str): The importable Python module path of the subgraph.

    Returns:
        str: A success message with the file path if the tool was created successfully,
             or an error message if the generation failed.
    """
    result = create_mcp_tool_logic(module_path)
    return result


# -------------------- MCP Tool Registration --------------------
# All new MCP-compatible tools should be added **below this line**.
# Each MCP tool must accept a single input argument named `state`.

from airas.features.analysis.analytic_subgraph.analytic_subgraph import AnalyticSubgraph


@mcp.tool(
    description="Takes a state dict with keys 'new_method', 'verification_policy', 'experiment_code', and 'output_text_data'; instantiates AnalyticSubgraph with a fixed llm_name ('o3-mini-2025-01-31'), runs the analysis to generate an 'analysis_report', and returns the updated state."
)
def analytic_subgraph(state: dict) -> dict:
    state = AnalyticSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.create.create_code_subgraph.create_code_subgraph import (
    CreateCodeSubgraph,
)


@mcp.tool(
    description="Takes a state dictionary with keys: new_method, experiment_code, github_repository, branch_name; creates and runs a CreateCodeSubgraph to push code to Devin and then check for its completion; returns the updated state."
)
def create_code_subgraph(state: dict) -> dict:
    state = CreateCodeSubgraph().run(state)
    return state


from airas.features.create.create_experimental_design_subgraph.create_experimental_design_subgraph import (
    CreateExperimentalDesignSubgraph,
)


@mcp.tool(
    description="Takes a state dict containing keys 'new_method', 'base_method_text', 'base_experimental_code', and 'base_experimental_info'. It instantiates the CreateExperimentalDesignSubgraph and runs it to generate additional keys 'verification_policy', 'experiment_details', and 'experiment_code' in the state, and then returns the updated state."
)
def create_experimental_design_subgraph(state: dict) -> dict:
    state = CreateExperimentalDesignSubgraph().run(state)
    return state


from airas.features.create.create_method_subgraph.create_method_subgraph import (
    CreateMethodSubgraph,
)


@mcp.tool(
    description="Takes a state dictionary with keys 'base_method_text' (a CandidatePaperInfo) and 'add_method_texts' (a list of CandidatePaperInfo), instantiates CreateMethodSubgraph with a fixed llm_name 'o3-mini-2025-01-31', runs the subgraph to generate a new method stored under 'new_method', and returns the updated state."
)
def create_method_subgraph(state: dict) -> dict:
    state = CreateMethodSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.create.fix_code_subgraph.fix_code_subgraph import FixCodeSubgraph


@mcp.tool(
    description="Takes input state with keys 'experiment_session_id', 'output_text_data', 'error_text_data', and 'executed_flag'; runs the FixCodeSubgraph to decide whether to fix the code using LLM and Devin, updating 'output_text_data', 'push_completion', and 'executed_flag'; returns the updated state."
)
def fix_code_subgraph(state: dict) -> dict:
    state = FixCodeSubgraph().run(state)
    return state


from airas.features.execution.github_actions_executor_subgraph.github_actions_executor_subgraph import (
    GitHubActionsExecutorSubgraph,
)


@mcp.tool(
    description="Takes a state dict with keys 'github_repository', 'branch_name', 'experiment_iteration', and 'push_completion'; executes the GitHub Actions workflow and then retrieves the corresponding results; returns the updated state including output_text_data, error_text_data, image_file_name_list, executed_flag, and an incremented experiment_iteration."
)
def github_actions_executor_subgraph(state: dict) -> dict:
    state = GitHubActionsExecutorSubgraph(gpu_enabled=False).run(state)
    return state


from airas.features.github.create_branch_subgraph import CreateBranchSubgraph


@mcp.tool(
    description="Takes a state dict with 'github_repository' and 'branch_name', creates a new branch using CreateBranchSubgraph with fixed configuration (new_branch_name='default_new_branch' and up_to_subgraph='default_subgraph'), and returns the state with the branch creation result."
)
def create_branch_subgraph(state: dict) -> dict:
    state = CreateBranchSubgraph(
        new_branch_name="default_new_branch", up_to_subgraph="default_subgraph"
    ).run(state)
    return state


from airas.features.github.github_download_subgraph import GithubDownloadSubgraph


@mcp.tool(
    description="This tool takes a state with 'github_repository' and 'branch_name' keys; it instantiates the GithubDownloadSubgraph to download the research history from the specified repository and branch, and returns the resulting state containing the 'research_history' field."
)
def github_download_subgraph(state: dict) -> dict:
    state = GithubDownloadSubgraph().run(state)
    return state


from airas.features.github.github_upload_subgraph import GithubUploadSubgraph


@mcp.tool(
    description="Takes a state dictionary with keys 'github_repository', 'branch_name', and 'subgraph_name' (additional keys are collected as cumulative output). It instantiates GithubUploadSubgraph, which processes the input by parsing the repository details, downloading the research history, merging with cumulative output, and uploading the merged data to GitHub. Returns the enriched state including fields like 'research_history' and 'github_upload_success'."
)
def github_upload_subgraph(state: dict) -> dict:
    state = GithubUploadSubgraph().run(state)
    return state


from airas.features.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)


@mcp.tool(
    description="Takes a state dictionary with keys 'github_repository' and 'branch_name', instantiates PrepareRepositorySubgraph using default template values, runs the subgraph, and returns the modified state."
)
def prepare_repository_subgraph(state: dict) -> dict:
    state = PrepareRepositorySubgraph().run(state)
    return state


from airas.features.publication.html_subgraph.html_subgraph import HtmlSubgraph


@mcp.tool(
    description="Takes a state dict with keys 'github_repository', 'branch_name', 'paper_content_with_placeholders', and 'references'. It instantiates an HtmlSubgraph using a fixed llm_name, processes the paper content to generate and render HTML, uploads the HTML to GitHub, and dispatches a workflow. The final state returned includes output fields such as 'full_html' and 'github_pages_url'."
)
def html_subgraph(state: dict) -> dict:
    state = HtmlSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.publication.latex_subgraph.latex_subgraph import LatexSubgraph


@mcp.tool(
    description="This tool takes a state dict with keys 'github_repository', 'branch_name', 'paper_content_with_placeholders', 'references', and 'image_file_name_list'. It instantiates the LatexSubgraph with a fixed LLM model 'o3-mini-2025-01-31' and executes its LaTeX generation workflow (including generating bibliography, converting content, assembling LaTeX, uploading files, and dispatching the GitHub workflow). It returns the original state updated with the output field 'tex_text', which contains the generated LaTeX document."
)
def latex_subgraph(state: dict) -> dict:
    state = LatexSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.publication.readme_subgraph.readme_subgraph import ReadmeSubgraph


@mcp.tool(
    description="Takes a state dictionary with keys 'github_repository', 'branch_name', 'paper_content', and 'experiment_devin_url'. It instantiates ReadmeSubgraph which splits 'github_repository' into 'github_owner' and 'repository_name', then uploads the README using 'Title' and 'Abstract' from 'paper_content'. Returns the state updated with 'readme_upload_result' along with other added execution fields."
)
def readme_subgraph(state: dict) -> dict:
    state = ReadmeSubgraph().run(state)
    return state


from airas.features.retrieve.retrieve_code_subgraph.retrieve_code_subgraph import (
    RetrieveCodeSubgraph,
)


@mcp.tool(
    description="Takes a state dict with keys 'base_github_url' and 'base_method_text', uses RetrieveCodeSubgraph to retrieve repository contents and extract experimental info, and returns the updated state with keys 'base_experimental_code' and 'base_experimental_info'."
)
def retrieve_code_subgraph(state: dict) -> dict:
    state = RetrieveCodeSubgraph().run(state)
    return state


from airas.features.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph import (
    RetrievePaperFromQuerySubgraph,
)


@mcp.tool(
    description="Takes a state dict with key 'base_queries' as input, runs the RetrievePaperFromQuerySubgraph using fixed parameters (llm_name, save_dir, and scrape_urls) to retrieve and process paper information, and returns the updated state containing keys such as 'base_github_url' and 'base_method_text'."
)
def retrieve_paper_from_query_subgraph(state: dict) -> dict:
    # Instantiate the subgraph with predetermined configuration
    subgraph = RetrievePaperFromQuerySubgraph(
        llm_name="o3-mini-2025-01-31",
        save_dir="/workspaces/airas/data",
        scrape_urls=["https://icml.cc/virtual/2024/papers.html?filter=title"],
    )
    state = subgraph.run(state)
    return state


from airas.features.retrieve.retrieve_related_paper_subgraph.retrieve_related_paper_subgraph import (
    RetrieveRelatedPaperSubgraph,
)


@mcp.tool(
    description="This tool takes a state dictionary with keys 'base_queries', 'base_github_url', 'base_method_text', and optionally 'add_queries'. It instantiates the RetrieveRelatedPaperSubgraph with fixed parameters to retrieve related paper information (including generated queries, add_github_urls, and add_method_texts) and returns the updated state."
)
def retrieve_related_paper_subgraph(state: dict) -> dict:
    state = RetrieveRelatedPaperSubgraph(
        llm_name="o3-mini-2025-01-31",
        save_dir="/workspaces/airas/data",
        scrape_urls=["https://icml.cc/virtual/2024/papers.html?filter=title"],
        add_paper_num=1,
    ).run(state)
    return state


from airas.features.write.citation_subgraph.citation_subgraph import CitationSubgraph


@mcp.tool(
    description="Takes a state dict with a 'paper_content' key (a dict of paper sections) as input, processes the content to embed citation placeholders, generate citation queries, retrieve references, and cleanse the text, then returns the state with updated keys 'paper_content_with_placeholders' and 'references'."
)
def citation_subgraph(state: dict) -> dict:
    state = CitationSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.write.writer_subgraph.writer_subgraph import WriterSubgraph


@mcp.tool(
    description="Takes a state dict with keys: base_method_text, new_method, verification_policy, experiment_details, experiment_code, output_text_data, analysis_report, image_file_name_list; instantiates a WriterSubgraph with llm_name 'o3-mini-2025-01-31' and refine_round 1, runs the subgraph, and returns the updated state."
)
def writer_subgraph(state: dict) -> dict:
    state = WriterSubgraph(llm_name="o3-mini-2025-01-31", refine_round=1).run(state)
    return state


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    mcp.run()
