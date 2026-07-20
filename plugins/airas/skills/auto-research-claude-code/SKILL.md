---
name: auto-research-claude-code
description: Run an end-to-end automated ML research project with the AIRAS MCP tools where Claude Code itself authors the generation steps (hypothesis, experimental design, analysis, paper) using AIRAS's curated prompts via get_generation_prompt — no LLM provider API key required. Use when the user wants automated research with AIRAS but no LLM provider key (OPENAI_API_KEY etc.) is configured, or when they want you to write the research artifacts yourself. If backend LLM keys are configured and preferred, use the auto-research skill instead.
---

# AIRAS automated research (Claude Code authoring mode)

You author every research artifact yourself, guided by AIRAS's curated
prompts. AIRAS provides retrieval, prompt assembly, and execution
infrastructure as MCP tools (server name: `airas`). No LLM provider API
key is needed; `GH_PERSONAL_ACCESS_TOKEN` is still required for
repository/experiment tools (credentials: `~/.airas/credentials.json`,
editable via `open_dashboard`).

## How authoring works

For each generation step, call
`get_generation_prompt(step, inputs)`. It returns:

- `prompt` — AIRAS's curated prompt, fully rendered from your inputs
  (the same template the backend LLM would use)
- `output_json_schema` — exactly the data format to produce
- `flow` — how the output feeds the next step

Follow the prompt and produce the output **in one pass**, matching the
schema. Steps: `research_queries`, `hypothesis`, `experimental_design`,
`experiment_analysis`, `paper_writing`, `latex_conversion`.

## Flow

1. **Discover**: author queries via
   `get_generation_prompt("research_queries", ...)` → `search_papers`
   (no key needed) → read papers with `fetch_paper_fulltext` (no key
   needed) and extract the study details yourself. (`retrieve_papers`
   needs a backend LLM key — do its extraction yourself in this mode.)
2. **Hypothesize & design**: author via
   `get_generation_prompt("hypothesis", ...)` then
   `get_generation_prompt("experimental_design", ...)` (ask the user
   about the compute environment; `retrieve_models` / `retrieve_datasets`
   list curated candidates, no key needed).
3. **Set up the experiment repository**: `prepare_repository`, then clone
   it locally with git.
4. **Write the experiment code yourself** in the clone. Read its
   `AGENTS.md` first — it defines the contract (allowed files, CLI shape,
   `sanity` / `pilot` / `full` modes, validation verdict lines, W&B
   conventions). For library-specific guidance (fine-tuning frameworks,
   distributed training, inference), `get_library_docs` (no key needed)
   returns each library's official docs and `llms.txt` endpoints — fetch
   those for current API usage instead of relying on memory. (The
   AI-Research-SKILLs library, which the template's code-generation
   workflows install on their runners, can also be installed locally:
   `npx @orchestra-research/ai-research-skills`.) Run
   `mode=sanity` locally until it prints `SANITY_VALIDATION: PASS`, then
   commit and push.
5. **Run experiments**: `dispatch_experiment` (async;
   `backend="github_actions"` or `"aixs"` with a `compute_type`). Poll
   `get_workflow_runs` (GitHub Actions) or `get_experiment_run_status`
   (either backend; returns stdout/stderr tails for debugging). Fix code
   locally and re-dispatch as needed.
6. **Analyze**: `fetch_experiment_results`, then author the analysis via
   `get_generation_prompt("experiment_analysis", ...)` (pass the code
   from your clone as `{"files": {"<path>": "<content>"}}`).
7. **Figures** (see conventions below).
8. **Write the paper**: `generate_bibfile` (no key needed) → author via
   `get_generation_prompt("paper_writing", ...)` → convert via
   `get_generation_prompt("latex_conversion", ...)`, embed into
   `template.tex` as its flow describes, save as
   `.research/latex/{template}/main.tex` in the clone and push with git.
9. **Publish**: use `open_in_overleaf` — it returns a link that creates an
   editable Overleaf project (pass `local_path` to export the local
   working tree without pushing; no GitHub token needed for that variant).
   In this mode Overleaf is the primary exit: `compile_latex` runs a
   LaTeX-fixing agent on GitHub Actions that requires an
   `ANTHROPIC_API_KEY` repository secret, which key-free setups don't
   have. Only suggest `compile_latex` if the user has set that secret.
10. **Persist**: `upload_research_history` saves the state;
    `download_research_history` restores it in a later session.

## Figure conventions

- Result charts: build a Vega-Lite spec (data inline under `data.values`)
  and `render_chart` it to `.research/results/chart/<name>.pdf` in the
  clone. Rendering is fully local; no API keys.
- Method diagrams: write text notation (mermaid / graphviz / d2 / …) and
  `render_diagram` it to `.research/results/diagram/<name>.pdf`. Uses
  https://kroki.io by default; `KROKI_BASE_URL` switches to self-hosted.
- Keep filenames unique, commit and push. `compile_latex` and
  `open_in_overleaf` collect every PDF under `.research/results/` into the
  paper's `images/` (structure preserved) — reference them in LaTeX as
  `images/<path>`, e.g. `images/chart/loss.pdf`.

## Notes

- Long-running tools return immediately; never block waiting. Poll between
  other work.
- All repository writes go through your local clone and git; there are no
  file-upload tools.
