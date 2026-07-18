---
name: airas-research
description: Run an end-to-end automated ML research project with the AIRAS MCP tools — from literature search and hypothesis generation to experiments on GitHub Actions/AIXS, figures, and a compiled paper. Use when the user wants to start or continue a research project with AIRAS, run automated research, reproduce/extend a paper experimentally, or asks how to use the airas MCP tools together.
---

# AIRAS research workflow

You drive the research; AIRAS provides retrieval, execution infrastructure,
and curated generation steps as MCP tools (server name: `airas`).

## Prerequisites

- Credentials live in `~/.airas/credentials.json`, re-read on every tool
  call. The easiest editor is the dashboard: run `open_dashboard` and open
  its API Keys page.
- `GH_PERSONAL_ACCESS_TOKEN` is required for repository/experiment tools.
  An LLM provider key (e.g. `OPENAI_API_KEY`) is required only for
  backend-LLM generation tools — without one, use host mode (below).

## Flow

1. **Discover**: `generate_research_queries` → `search_papers` →
   `retrieve_papers` (structured study data).
2. **Hypothesize & design**: `generate_hypothesis` →
   `generate_experimental_design` (pass `compute_environment` so the design
   fits the hardware; `retrieve_models` / `retrieve_datasets` list curated
   candidates).
3. **Set up the experiment repository**: `prepare_repository`, then clone
   it locally with git.
4. **Write the experiment code yourself** in the clone. Read its
   `AGENTS.md` first — it defines the contract (allowed files, CLI shape,
   `sanity` / `pilot` / `full` modes, validation verdict lines, W&B
   conventions). Run `mode=sanity` locally until it prints
   `SANITY_VALIDATION: PASS`, then commit and push.
5. **Run experiments**: `dispatch_experiment` (async;
   `backend="github_actions"` or `"aixs"` with a `compute_type`). Poll
   `get_workflow_runs` (GitHub Actions) or `get_experiment_run_status`
   (either backend; returns stdout/stderr tails for debugging). Fix code
   locally and re-dispatch as needed.
6. **Analyze**: `fetch_experiment_results` → `analyze_experiment`
   (pass the experiment code from your clone as
   `{"files": {"<path>": "<content>"}}`).
7. **Figures**: create them yourself — see the `airas-figures` skill for
   the conventions (`render_chart` / `render_diagram`, output locations).
8. **Write the paper**: `generate_bibfile` → `generate_paper` →
   `generate_latex`. Write the returned LaTeX to
   `.research/latex/{template}/main.tex` in the clone and push with git.
9. **Publish (two independent exits, use either or both)**:
   `compile_latex` builds the PDF on GitHub Actions; `open_in_overleaf`
   returns a link that creates an editable Overleaf project (pass
   `local_path` to export the local working tree without pushing —
   no GitHub token needed).
10. **Persist**: `upload_research_history` saves the state;
    `download_research_history` restores it in a later session.

## Host mode (no LLM API key)

Every generation step is dual-mode. If no LLM provider key is configured
(or your own conversation context should inform the writing), call
`get_generation_prompt(step, inputs)` — it returns AIRAS's curated prompt,
an `output_json_schema` describing exactly the data format to produce, and
a `flow` note. Author the artifact yourself in one pass. Steps:
`research_queries`, `hypothesis`, `experimental_design`,
`experiment_analysis`, `paper_writing`, `latex_conversion`.

## Notes

- Long-running tools return immediately; never block waiting. Poll between
  other work.
- All repository writes go through your local clone and git; there are no
  file-upload tools.
