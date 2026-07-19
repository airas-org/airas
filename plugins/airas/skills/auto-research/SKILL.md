---
name: auto-research
description: Run an end-to-end automated ML research project with the AIRAS MCP tools, using backend LLM API keys for the generation steps (hypothesis, experimental design, analysis, paper writing). Use when the user wants to start or continue automated research with AIRAS and LLM provider API keys (OPENAI_API_KEY etc.) are configured in ~/.airas/credentials.json. If no LLM provider key is available, use the auto-research-claude-code skill instead.
---

# AIRAS automated research (backend-LLM mode)

You drive the research; AIRAS provides retrieval, curated generation steps
(run on its backend LLM), and execution infrastructure as MCP tools
(server name: `airas`).

## Prerequisites

- Credentials live in `~/.airas/credentials.json`, re-read on every tool
  call. The easiest editor is the dashboard: run `open_dashboard` and open
  its API Keys page.
- This mode requires an LLM provider key (e.g. `OPENAI_API_KEY`) for the
  generation tools, and `GH_PERSONAL_ACCESS_TOKEN` for
  repository/experiment tools.

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
   conventions). Check `list_domain_knowledge` / `get_domain_knowledge`
   for AIRAS engineering notes relevant to the design (reproducibility,
   VRAM budgeting, CI constraints, results conventions). For
   library-specific guidance (fine-tuning frameworks, distributed
   training, inference), the AI-Research-SKILLs library can be installed
   locally (`npx @orchestra-research/ai-research-skills`) — the
   template's own code-generation workflows already use it. Run
   `mode=sanity` locally until it prints `SANITY_VALIDATION: PASS`, then
   commit and push.
5. **Run experiments**: `dispatch_experiment` (async;
   `backend="github_actions"` or `"aixs"` with a `compute_type`). Poll
   `get_workflow_runs` (GitHub Actions) or `get_experiment_run_status`
   (either backend; returns stdout/stderr tails for debugging). Fix code
   locally and re-dispatch as needed.
6. **Analyze**: `fetch_experiment_results` → `analyze_experiment`
   (pass the experiment code from your clone as
   `{"files": {"<path>": "<content>"}}`).
7. **Figures** (see conventions below).
8. **Write the paper**: `generate_bibfile` → `generate_paper` →
   `generate_latex`. Write the returned LaTeX to
   `.research/latex/{template}/main.tex` in the clone and push with git.
9. **Publish (two independent exits, use either or both)**:
   `compile_latex` builds the PDF on GitHub Actions; `open_in_overleaf`
   returns a link that creates an editable Overleaf project (pass
   `local_path` to export the local working tree without pushing).
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
