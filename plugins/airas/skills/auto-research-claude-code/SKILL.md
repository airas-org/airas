---
name: auto-research-claude-code
description: Run an end-to-end automated research project with the AIRAS MCP tools where Claude Code itself authors the generation steps (hypothesis, experimental design, analysis, paper) using AIRAS's curated prompts via get_generation_prompt — no LLM provider API key required. Use when the user wants automated research with AIRAS but no LLM provider key (OPENAI_API_KEY etc.) is configured, when they want you to write the research artifacts yourself, or as a fallback when the backend generation tools are configured but failing or unreliable (timeouts on long-reasoning models, retrieval returning empty studies) — get_generation_prompt uses the same curated prompts, so switching modes loses nothing but the automation. If backend LLM keys are configured and working, use the auto-research skill instead.
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
- `input_json_schema` — the exact shape of `inputs` for that step
- `output_json_schema` — exactly the data format to produce
- `flow` — how the output feeds the next step

Follow the prompt and produce the output **in one pass**, matching the
schema. Steps: `research_queries`, `hypothesis`, `experimental_design`,
`experiment_analysis`, `paper_writing`, `latex_conversion`.

Several inputs have to be assembled by hand in this mode. Call
`get_input_schema(step)` before you build one rather than discovering its
shape from a validation error. The two that catch people out:

- `research_study_list` entries are `ResearchStudy` objects, which share no
  key names with `search_papers` rows: a row's `authors`, `citations` and
  `arxiv_id` belong under `meta_data`. Only `title` is required, so
  `{"title": ..., "abstract": ...}` is a valid study — you never have to
  invent a full text for a paper you did not read.
- `compute_environment` is an object, not a string. Include `arch`
  (`x86_64` / `aarch64`) whenever you know it; it decides whether a
  dependency has an installable wheel at all.

## Write in Japanese

The people reviewing this work will not always have the domain knowledge
to judge a claim — about protein-ligand scoring, say — on sight. A
plausible-sounding mistake is only catchable if they can read it
comfortably, so **write every artifact a human is meant to check in
Japanese**: the hypothesis, the experimental design, the analysis report,
and the paper itself, through to the PDF.

Two things stay English because they are identifiers rather than prose:
`primary_metric` / `supporting_metrics`, which are parsed downstream to
compute the GAP, and BibTeX citation keys.

A Japanese paper needs LuaTeX — pdflatex raises `LaTeX Error: Unicode
character` for every Japanese character and leaves the text out of the
PDF. `verify_latex` picks the engine from the document, so nothing has to
be configured, but the preamble is yours to write. Start `main.tex` with:

```latex
\documentclass[11pt]{article}
\usepackage{luatexja-fontspec}
\setmainjfont{IPAexMincho}
\setsansjfont{IPAexGothic}
```

If `verify_latex` reports that lualatex is missing, install it:
`apt-get install texlive-luatex texlive-lang-japanese`.

The bundled templates (`iclr2024`, `mdpi`, `agents4science_2025`) are
English conference styles with no CJK support, so a Japanese paper does
not use them — write your own preamble as above and keep the structure
(title, abstract, numbered sections, figures, bibliography). Translate to
English only when the user asks; treat that as a rendering rather than a
rewrite, since no claim, number or citation should change on the way.

## Flow

1. **Discover**: author queries via
   `get_generation_prompt("research_queries", ...)` → `search_papers`
   (no key needed) → read papers with `fetch_paper_fulltext` (no key
   needed) and extract the study details yourself. Pass **both** the `doi`
   and the `pdf_url` from the `search_papers` row when it gave you both:
   a DOI alone returns only the abstract for anything outside Semantic
   Scholar's open-access index, bioRxiv included. Full texts run to tens of
   thousands of characters, so keep `max_chars` at its default and raise it
   only for a paper you must read in full. (`retrieve_papers` needs a
   backend LLM key — do its extraction yourself in this mode.)
2. **Hypothesize & design**: author via
   `get_generation_prompt("hypothesis", ...)` then
   `get_generation_prompt("experimental_design", ...)`. Establish the
   compute environment before designing — ask the user if the target is not
   already known, and record `arch` along with the GPU. `retrieve_models` /
   `retrieve_datasets` list curated candidates (no key needed); the design
   prompt's built-in MODEL/DATASET lists are language-model defaults, so for
   any other field pass the candidates you retrieved rather than following
   those lists.
3. **Set up the experiment repository**: `prepare_repository` — it returns
   `clone_url` — then clone it locally with git. Write the hypothesis and
   the experimental design to `.research/research_history.json` and push
   before generating any code: the repository's own code-generation
   workflows read the research context from that file, and it ships empty.
   `upload_research_history` does this against the pushed branch.
4. **Write the experiment code yourself** in the clone. Read its
   `AGENTS.md` first — it is the contract the runners hold you to, and it
   is more specific than anything here: which files you may touch, the
   exact CLI invocations, what each of `sanity` / `pilot` / `full` must
   scale to, the machine-parsed `SANITY_VALIDATION: PASS` /
   `PILOT_VALIDATION` verdict lines, the run-id naming rule, the W&B
   namespaces, and what `src/evaluate.py` must write. The shape it fixes:

   ```
   uv run python -u -m src.main run={run_id} results_dir=.research/results mode={mode}
   ```

   The template ships `src/*.py` empty and a `pyproject.toml` that is a
   single comment, so `uv sync` does not work until you write a real one —
   budget for that before the first run.
   For library-specific guidance (fine-tuning frameworks,
   distributed training, inference), `get_library_docs` (no key needed)
   returns each library's official docs and `llms.txt` endpoints — fetch
   those for current API usage instead of relying on memory. (The
   AI-Research-SKILLs library, which the template's code-generation
   workflows install on their runners, can also be installed locally:
   `npx @orchestra-research/ai-research-skills`.) Run
   `mode=sanity` locally until it prints `SANITY_VALIDATION: PASS`, then
   commit and push.

   Two things a local sanity run cannot tell you. It cannot catch an
   architecture mismatch: if the target is arm64 and you are on x86, a
   dependency can resolve locally and have no wheel for the target —
   `--dry-run` resolving is not proof it installs, so check the wheels in
   `uv.lock` against the target architecture. And the image is built from a
   *regenerated* Dockerfile, not yours verbatim: instructions whose purpose
   is legible survive, unexplained ones may be dropped, and undeclared
   dependencies get invented unpinned. Comment *why* each Dockerfile
   instruction is needed, pin dependencies in `pyproject.toml`, and commit
   `uv.lock` — that leaves nothing to invent.
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
6. **Analyze**: `fetch_experiment_results`, then author the analysis via
   `get_generation_prompt("experiment_analysis", ...)` (pass the code
   from your clone as `{"files": {"<path>": "<content>"}}`).
7. **Figures** (see conventions below).
8. **Write the paper**: `generate_bibfile` (no key needed) → author via
   `get_generation_prompt("paper_writing", ...)` → convert via
   `get_generation_prompt("latex_conversion", ...)`, embed into
   `template.tex` as its flow describes, and save **two** files in the
   clone: the LaTeX as `.research/latex/{template}/main.tex`, and the
   bibliography from `generate_bibfile` as
   `.research/latex/{template}/references.bib`. The template ships a
   `references.bib` containing one placeholder entry, so skipping the
   second file makes every `\cite` render as `?`. Push both with git.
9. **Verify before publishing**: `verify_latex` (pass `local_path` to check
   the working tree with no push and no keys). It compiles the paper and
   reports `ok`, `page_count`, `undefined_citations`, `undefined_references`
   and `missing_figures`. Do not treat the paper as finished while `ok` is
   false — a `?` citation and an absent figure both still produce a PDF, so
   nothing else in the pipeline will notice them.
10. **Publish**: use `open_in_overleaf` — it returns a link that creates an
    editable Overleaf project (pass `local_path` to export the local
    working tree without pushing; no GitHub token needed for that variant).
    Overleaf is an **export**, not a loop: nothing reads a project back, and
    each click creates a new one, so everything you want in the paper must
    be right before this point. `compile_latex` runs a LaTeX-fixing agent on
    GitHub Actions that requires an `ANTHROPIC_API_KEY` repository secret,
    which key-free setups do not have; only suggest it if the user has set
    that secret. It materializes the figures itself at build time, so they
    only need to have been pushed.
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
  same relative path. Reference them in LaTeX as `images/<path>` — copy the
  path you were given rather than reducing it to the bare filename, since
  two runs can each produce `accuracy.pdf` and only the full path resolves.

## Running unattended

- Long-running tools return immediately; never block waiting. Poll between
  other work.
- Most repository writes go through your local clone and git; the exception is `upload_research_history`, which commits `.research/research_history.json` via an MCP tool. There are no general-purpose file-upload tools.
- When a step fails, go back only as far as the failure requires: a failed
  experiment run means fixing code and re-dispatching (step 5), not
  re-deriving the hypothesis. Re-run a generation step only when its
  *inputs* changed.
- Several tools report a problem instead of raising it, and those are the
  ones that quietly produce a worthless paper. Check them rather than
  assuming success: `search_papers` returns `search_errors` per source;
  `fetch_paper_fulltext` returns `status` (`abstract_only` means you are
  about to write about a paper you only skimmed) and `truncated`;
  `verify_latex` returns `ok`.
- Stop and ask the user when the research direction is genuinely
  underdetermined, or when a step has failed the same way twice — repeating
  it a third time rarely differs.
