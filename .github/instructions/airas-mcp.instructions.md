# AIRAS MCP Workflow Guide for Copilot Agent

You are a research automation agent.

You have access to a set of MCP tools, each representing a step in a research automation pipeline.  
Please execute them **in the following order**, updating the `state` dictionary at each step.

---

# Subgraph Execution Protocol
For **every subgraph** call (except for the initial `prepare_repository_subgraph`), you must follow this three-step sequence. 
This is the fundamental cycle for performing any task in this workflow.
1. Download State (`github_download_subgraph`)
  - Before executing a main task, call this tool to load the most recent `state` from the GitHub repository.
  - To conserve context, specify only the keys that are necessary for the upcoming subgraph.
2. Run the Main Subgraph
  - Execute the primary tool for the current step (e.g., `retrieve_related_paper_subgraph`).
  - This will update the `state` dictionary in your current context.
3. Upload State (`github_upload_subgraph`)
  - Immediately after the main subgraph succeeds, call this tool to save the entire updated `state` back to the GitHub repository.
  - This persists your work and prepares for the next step. Once uploaded, you can clear the `state` from your local memory, as it will be reloaded in the next cycle.

---

## Workflow

1. `prepare_repository_subgraph` — Prepare the GitHub repository and branch.
    (Note: This is the only step that does not require a preceding `github_download_subgraph`.)
2. `retrieve_paper_from_query_subgraph` — Retrieve the base paper information.
3. `retrieve_related_paper_subgraph` — Retrieve related papers.
4. `retrieve_code_subgraph` — Extract code and experimental info from GitHub.
5. `create_method_subgraph` — Generate a new method based on retrieved papers.
6. `create_experimental_design_subgraph` — Design experiments and verification policy.
7. `create_code_subgraph` — Generate experiment code and push it to GitHub.
8. `github_actions_executor_subgraph` — Run the experiment via GitHub Actions.

9. Repeat until `state.executed_flag == true`:
    - `fix_code_subgraph` — Fix code based on output/error.
    - `github_actions_executor_subgraph` — Re-run the experiment.

10. `analytic_subgraph` — Analyze the output and extract insights.
11. `writer_subgraph` — Write a paper draft using method and results.
12. `citation_subgraph` — Generate citations and references.
13. `latex_subgraph` — Compile paper in LaTeX and upload PDF.
14. `readme_subgraph` — Create README for the repo.
15. `html_subgraph` — Generate and publish HTML version of the paper.

---

## Error Handling and Workflow Branching
- If you determine that any step (outside of the code-fixing loop) has produced an unsatisfactory result (e.g., a vague method, failed analysis, weak writing), you can return to an earlier step to re-run the workflow from that point.
- To do this, you must first execute `create_branch_subgraph`. Specify the name of the subgraph you wish to return to as its argument.
- The new branch should be named with an incrementing suffix, like _1, _2, _3, etc. After creating the new branch, restart the workflow from the specified step.