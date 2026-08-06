---
name: auto-research
description: Run an end-to-end automated research project with the AIRAS MCP tools, using backend LLM API keys for the generation steps (hypothesis, experimental design, analysis, paper writing). Use when the user wants to start or continue automated research with AIRAS and LLM provider API keys (OPENAI_API_KEY etc.) are configured in ~/.airas/credentials.json. If no LLM provider key is available, or the backend generation tools are configured but failing (timeouts, retrieval returning empty studies), use the auto-research-claude-code skill instead.
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
   `retrieve_papers` (structured study data). `retrieve_papers` resolves
   each title through an LLM web search, so check what came back: a study
   whose `full_text` is empty and whose `llm_extracted_info` fields all read
   `[Unavailable]` means resolution failed, and feeding it onward produces a
   hypothesis with nothing behind it. When that happens, use
   `fetch_paper_fulltext` with the identifiers `search_papers` gave you and
   assemble the studies yourself.
2. **Hypothesize & design**: `generate_hypothesis` →
   `generate_experimental_design` (pass `compute_environment` so the design
   fits the hardware — include `arch`, which decides whether a dependency
   has an installable wheel at all; `retrieve_models` / `retrieve_datasets`
   list curated candidates).
3. **Set up the experiment repository**: `prepare_repository` — it returns
   `clone_url` — then clone it locally with git. Push the hypothesis and
   experimental design to `.research/research_history.json` with
   `upload_research_history` before generating any code: the repository's
   own code-generation workflows read the research context from that file,
   and it ships empty.
4. **Write the experiment code yourself** in the clone. Read its
   `AGENTS.md` first — it is the contract the runners hold you to: which
   files you may touch, the exact CLI invocations, what each of `sanity` /
   `pilot` / `full` must scale to, the machine-parsed
   `SANITY_VALIDATION: PASS` / `PILOT_VALIDATION` verdict lines, the
   run-id naming rule, the W&B namespaces, and what `src/evaluate.py` must
   write. The shape it fixes:

   ```
   uv run python -u -m src.main run={run_id} results_dir=.research/results mode={mode}
   ```

   The template ships `src/*.py` empty and a `pyproject.toml` that is a
   single comment, so `uv sync` does not work until you write a real one.
   For library-specific guidance (fine-tuning
   frameworks, distributed training, inference), `get_library_docs` returns
   each library's official docs and `llms.txt` endpoints — fetch those for
   current API usage instead of relying on memory. (The AI-Research-SKILLs
   library, which the template's code-generation workflows install on their
   runners, can also be installed locally:
   `npx @orchestra-research/ai-research-skills`.) Run
   `mode=sanity` locally until it prints `SANITY_VALIDATION: PASS`, then
   commit and push.

   Two things a local sanity run cannot tell you. It cannot catch an
   architecture mismatch: if the target is arm64 and you are on x86, a
   dependency can resolve locally and have no wheel for the target —
   `--dry-run` resolving is not proof it installs. And the image is built
   from a *regenerated* Dockerfile, not yours verbatim: instructions whose
   purpose is legible survive, unexplained ones may be dropped, and
   undeclared dependencies get invented unpinned. Comment *why* each
   Dockerfile instruction is needed, pin dependencies in `pyproject.toml`,
   and commit `uv.lock`.
5. **Run experiments**: `dispatch_experiment` (async;
   `backend="github_actions"` or `"seyval"` with a `compute_type`). Poll
   `get_workflow_runs` (GitHub Actions) or `get_experiment_run_status`
   (either backend; returns stdout/stderr tails for debugging). Fix code
   locally and re-dispatch as needed. On Seyval, resolve the target with
   `list_computes` rather than reusing an id from an earlier session — ids
   are scoped per environment and workspace — and note that omitting
   `compute_id` sends the run to Seyval-managed compute rather than a BYO
   cluster. Results stay on Seyval's side, so `import_run_outputs` has to
   run before `fetch_experiment_results`, which reads the repository. If
   the experiment does not use Weights & Biases, pass `required_env_vars=[]`
   rather than registering a dummy `WANDB_API_KEY`.
6. **Analyze**: `fetch_experiment_results` → `analyze_experiment`
   (pass the experiment code from your clone as
   `{"files": {"<path>": "<content>"}}`).
7. **Figures** (see conventions below).
8. **Write the paper**: `generate_bibfile` → `generate_paper` →
   `generate_latex`. Save **two** files in the clone: the returned LaTeX as
   `.research/latex/{template}/main.tex`, and the bibliography from
   `generate_bibfile` as `.research/latex/{template}/references.bib`. The
   template ships a `references.bib` containing one placeholder entry, so
   skipping the second file makes every `\cite` render as `?`. Push both
   with git.
9. **Verify before publishing**: `verify_latex` (pass `local_path` to check
   the working tree without pushing). It compiles the paper and reports
   `ok`, `page_count`, `undefined_citations`, `undefined_references` and
   `missing_figures`. Do not treat the paper as finished while `ok` is
   false — a `?` citation and an absent figure both still produce a PDF.
10. **Publish (two independent exits, use either or both)**:
    `compile_latex` builds the PDF on GitHub Actions — it materializes the
    pushed figures itself, and its return value is a dispatch receipt
    rather than a build result. `open_in_overleaf` returns a link that creates an editable
    Overleaf project (pass `local_path` to export the local working tree
    without pushing); it is an export, not a loop — nothing reads a project
    back, and each click creates a new one.
11. **Persist**: `upload_research_history` saves the state;
    `download_research_history` restores it in a later session.

## Figure conventions

- Result charts: build a Vega-Lite spec (data inline under `data.values`)
  and `render_chart` it to `.research/results/chart/<name>.pdf` in the
  clone. Rendering is fully local; no API keys.
- Method diagrams: write text notation (mermaid / graphviz / d2 / …) and
  `render_diagram` it to `.research/results/diagram/<name>.pdf`. Uses
  https://kroki.io by default; `KROKI_BASE_URL` switches to self-hosted.
- Commit and push. `compile_latex` and `open_in_overleaf` collect every PDF
  under `.research/results/` into the paper's `images/` with the directory
  structure preserved, and `fetch_experiment_results` reports figures by the
  same relative path. Reference them in LaTeX as `images/<path>` — use the
  path you were given rather than the bare filename, since two runs can each
  produce `accuracy.pdf` and only the full path resolves.

## Notes

- Long-running tools return immediately; never block waiting. Poll between
  other work.
- Most repository writes go through your local clone and git; the exception is `upload_research_history`, which commits `.research/research_history.json` via an MCP tool. There are no general-purpose file-upload tools.
- Several tools report a problem instead of raising it, and those are the
  ones that quietly produce a worthless paper. Check them rather than
  assuming success: `search_papers` returns `search_errors` per source;
  `retrieve_papers` returns `[Unavailable]` fields on failure;
  `fetch_paper_fulltext` returns `status` and `truncated`; `verify_latex`
  returns `ok`.
