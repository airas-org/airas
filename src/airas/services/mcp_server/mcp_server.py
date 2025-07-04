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
    description="This tool takes a state dictionary with keys 'new_method', 'verification_policy', 'experiment_code', and 'output_text_data', runs the analytic subgraph with a predefined llm_name, and returns the state augmented with an 'analysis_report'."
)
def analytic_subgraph(state: dict) -> dict:
    state = AnalyticSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.create.create_code_subgraph.create_code_subgraph import (
    CreateCodeSubgraph,
)


@mcp.tool(
    description="Takes a state dict with keys: new_method, experiment_code, github_repository, branch_name; executes the CreateCodeSubgraph to push code and check devin completion; returns updated state with push_completion, experiment_session_id, experiment_devin_url, and experiment_iteration."
)
def create_code_subgraph(state: dict) -> dict:
    state = CreateCodeSubgraph().run(state)
    return state


from airas.features.create.create_experimental_design_subgraph.create_experimental_design_subgraph import (
    CreateExperimentalDesignSubgraph,
)


@mcp.tool(
    description="Takes a state dictionary with keys 'new_method', 'base_method_text', 'base_experimental_code', and 'base_experimental_info'; runs the CreateExperimentalDesignSubgraph subgraph which generates 'verification_policy', 'experiment_details', and 'experiment_code'; and returns the updated state dictionary."
)
def create_experimental_design_subgraph(state: dict) -> dict:
    state = CreateExperimentalDesignSubgraph().run(state)
    return state


from airas.features.create.create_method_subgraph.create_method_subgraph import (
    CreateMethodSubgraph,
)


@mcp.tool(
    description="This tool takes as input a state dictionary with keys 'base_method_text' and 'add_method_texts', uses CreateMethodSubgraph with a fixed LLM model 'o3-mini-2025-01-31' to generate a new method, and returns the updated state including the 'new_method' key."
)
def create_method_subgraph(state: dict) -> dict:
    state = CreateMethodSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.create.fix_code_subgraph.fix_code_subgraph import FixCodeSubgraph


@mcp.tool(
    description="This tool takes a state dictionary with keys 'experiment_session_id', 'output_text_data', 'error_text_data', and 'executed_flag'; it instantiates the FixCodeSubgraph, runs its pipeline to decide whether code fixing is needed and to process the fix, and then returns the updated state."
)
def fix_code_subgraph(state: dict) -> dict:
    state = FixCodeSubgraph().run(state)
    return state


from airas.features.execution.github_actions_executor_subgraph.github_actions_executor_subgraph import (
    GitHubActionsExecutorSubgraph,
)


@mcp.tool(
    description="This tool takes as input a state dictionary containing 'github_repository', 'branch_name', 'experiment_iteration', and 'push_completion'. It instantiates the GitHubActionsExecutorSubgraph with a fixed GPU setting (e.g., gpu_enabled=False), runs the subgraph workflow on the provided state, and returns the updated state with execution results."
)
def github_actions_executor_subgraph(state: dict) -> dict:
    state = GitHubActionsExecutorSubgraph(gpu_enabled=False).run(state)
    return state


from airas.features.github.create_branch_subgraph import CreateBranchSubgraph


@mcp.tool(
    description="Takes a dictionary with keys 'github_repository' and 'branch_name'; instantiates the subgraph with fixed parameters (new_branch_name set to 'new_branch' and up_to_subgraph set to 'create_branch_subgraph'), runs the graph to create a new branch, and returns the updated state."
)
def create_branch_subgraph(state: dict) -> dict:
    state = CreateBranchSubgraph(
        new_branch_name="new_branch", up_to_subgraph="create_branch_subgraph"
    ).run(state)
    return state


from airas.features.github.github_download_subgraph import GithubDownloadSubgraph


@mcp.tool(
    description="This tool accepts a state dictionary containing 'github_repository' (formatted as 'owner/repo') and 'branch_name'. It instantiates the GithubDownloadSubgraph, runs it to download the research history from the specified GitHub repository, and returns the final state with the research history."
)
def github_download_subgraph(state: dict) -> dict:
    state = GithubDownloadSubgraph().run(state)
    return state


from airas.features.github.github_upload_subgraph import GithubUploadSubgraph


@mcp.tool(
    description="Takes a state dictionary with keys like 'github_repository', 'branch_name', and 'subgraph_name', instantiates the GithubUploadSubgraph which downloads the research history, merges it with cumulative output, uploads the merged history to GitHub, and returns the updated state."
)
def github_upload_subgraph(state: dict) -> dict:
    state = GithubUploadSubgraph().run(state)
    return state


from airas.features.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)


@mcp.tool(
    description="This tool takes a state dictionary with 'github_repository' and 'branch_name'. It prepares the GitHub repository by initializing repository details, checking if the repository is created from a template, creating it if necessary, checking branch existence, and creating the branch if needed, then returns the updated state."
)
def prepare_repository_subgraph(state: dict) -> dict:
    state = PrepareRepositorySubgraph().run(state)
    return state


from airas.features.publication.html_subgraph.html_subgraph import HtmlSubgraph


@mcp.tool(
    description="Takes a state dictionary containing GitHub repository details, branch name, paper content with placeholders, and references; it runs the HTML subgraph workflow to convert the content to HTML, render and upload it, and dispatch a workflow, returning the state with generated HTML and GitHub Pages URL."
)
def html_subgraph(state: dict) -> dict:
    state = HtmlSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.publication.latex_subgraph.latex_subgraph import LatexSubgraph


@mcp.tool(
    description="Takes a state dict with GitHub repository info and publication content; instantiates LatexSubgraph with a fixed LLM name ('o3-mini-2025-01-31'), processes the LaTeX subgraph (bibliography generation, LaTeX conversion, assembly, file upload, and workflow dispatch), and returns the updated state including the generated tex_text."
)
def latex_subgraph(state: dict) -> dict:
    state = LatexSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.publication.readme_subgraph.readme_subgraph import ReadmeSubgraph


@mcp.tool(
    description="This tool takes a state dictionary as input with keys including 'github_repository', 'branch_name', 'paper_content', 'output_text_data', and 'experiment_devin_url'. It instantiates the ReadmeSubgraph, processes the readme upload, and returns the updated state including the 'readme_upload_result'."
)
def readme_subgraph(state: dict) -> dict:
    state = ReadmeSubgraph().run(state)
    return state


from airas.features.retrieve.retrieve_code_subgraph.retrieve_code_subgraph import (
    RetrieveCodeSubgraph,
)


@mcp.tool(
    description="This tool receives a state dictionary containing the input fields 'base_github_url' and 'base_method_text'. It instantiates the RetrieveCodeSubgraph (which retrieves the repository contents and extracts experimental code/information) and executes it, updating the state with fields such as 'repository_content_str', 'base_experimental_code', and 'base_experimental_info'. It returns the updated state as-is."
)
def retrieve_code_subgraph(state: dict) -> dict:
    state = RetrieveCodeSubgraph().run(state)
    return state


from airas.features.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph import (
    RetrievePaperFromQuerySubgraph,
)


@mcp.tool(
    description="Takes a state dictionary with a 'base_queries' field (list of strings), instantiates the RetrievePaperFromQuerySubgraph with fixed llm_name, save_dir, and scrape_urls, runs the subgraph to process the query and augment the state, and returns the updated state."
)
def retrieve_paper_from_query_subgraph(state: dict) -> dict:
    state = RetrievePaperFromQuerySubgraph(
        llm_name="o3-mini-2025-01-31",
        save_dir="/workspaces/airas/data",
        scrape_urls=["https://icml.cc/virtual/2024/papers.html?filter=title"],
    ).run(state)
    return state


from airas.features.retrieve.retrieve_related_paper_subgraph.retrieve_related_paper_subgraph import (
    RetrieveRelatedPaperSubgraph,
)


@mcp.tool(
    description="Takes a state dictionary containing base_queries, base_github_url, base_method_text, and optionally add_queries, runs the RetrieveRelatedPaperSubgraph to retrieve related paper information, and returns the updated state with generated queries, github urls, and method texts."
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
    description="Takes a state dictionary containing 'paper_content' (and related fields), runs the citation subgraph to embed placeholders, generate citation queries, and fetch references, then returns the updated state."
)
def citation_subgraph(state: dict) -> dict:
    state = CitationSubgraph(llm_name="o3-mini-2025-01-31").run(state)
    return state


from airas.features.write.writer_subgraph.writer_subgraph import WriterSubgraph


@mcp.tool(
    description="This tool takes a state dictionary containing the initial inputs for the writer subgraph, instantiates the WriterSubgraph with a fixed LLM name ('o3-mini-2025-01-31') and refine_round (1), processes the state to generate a note and paper content, and returns the updated state."
)
def writer_subgraph(state: dict) -> dict:
    state = WriterSubgraph(llm_name="o3-mini-2025-01-31", refine_round=1).run(state)
    return state


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    mcp.run(transport="stdio")
