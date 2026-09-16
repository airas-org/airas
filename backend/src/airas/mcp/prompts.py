"""Guided workflows offered to MCP clients as prompts."""

from airas.mcp.app import mcp


@mcp.prompt(title="Start an AIRAS research project")
def start_research(research_topic: str) -> str:
    """Kick off an end-to-end automated research project on a topic."""
    return f"""\
Run an end-to-end automated research project with the AIRAS MCP tools on \
this topic: {research_topic}

Follow this flow, checking in with me at each major decision:

1. Discover: generate_research_queries -> search_papers -> retrieve_papers.
2. Hypothesize & design: generate_hypothesis -> \
generate_experimental_design (ask me about the compute environment first; \
retrieve_models / retrieve_datasets list curated candidates).
3. Set up: prepare_repository, then clone the experiment repository locally.
4. Write the experiment code yourself in the clone. Read its AGENTS.md \
for the contract. For library-specific guidance, get_library_docs \
returns each library's official docs and llms.txt endpoints — fetch \
those for current API usage instead of relying on memory. Run \
mode=sanity locally until it prints SANITY_VALIDATION: PASS, then \
commit and push.
5. Run: dispatch_experiment (async). Poll get_workflow_runs or \
get_experiment_run_status between other work; debug from the stderr tail.
6. Analyze: fetch_experiment_results -> analyze_experiment (pass the code \
from the clone as {{"files": {{path: content}}}}).
7. Figures: build Vega-Lite specs and render_chart into \
.research/results/chart/, diagrams via render_diagram into \
.research/results/diagram/ (PDF, unique names), then git push. They are \
collected into the paper automatically.
8. Write: generate_bibfile -> generate_paper -> generate_latex; save the \
LaTeX as .research/latex/{{template}}/main.tex in the clone and push.
9. Publish: compile_latex (PDF on GitHub Actions) and/or open_in_overleaf \
(show me the link; local_path exports without pushing).
10. Persist: upload_research_history.

Every backend-LLM generation tool (generate_research_queries, \
generate_hypothesis, generate_experimental_design, analyze_experiment, \
generate_paper, generate_latex, compile_latex, retrieve_papers) now takes a \
required `model` argument — there is no default. Call get_available_llms \
first to see which models the configured API keys allow, and pass one; a \
model that cannot do a step's required structured output is rejected up front.

If no LLM provider key is configured, generation tools fail — in that case \
call get_generation_prompt(step, inputs) and author the artifact yourself \
following its prompt, output_json_schema, and flow.
"""
