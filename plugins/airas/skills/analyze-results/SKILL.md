---
name: analyze-results
description: Read imported experiment results, author the analysis with AIRAS's curated prompt, and produce the figures (verifiable charts and method diagrams). Use to analyze experiment outputs or make the paper's figures.
---

# Analyze results & make figures

Needs imported results under `.research/results/` in a clone.

1. **Produce the metrics mechanically with airas-eval.** Metrics are
   never computed by hand: the template ships a Makefile wired to
   [airas-eval](https://github.com/airas-org/airas-eval), a trusted,
   versioned scoring layer that computes a fixed metric set per task
   type from the raw predictions — run

   ```
   make evaluate RUN_ID=<run_id>
   ```

   per imported run (the plan lives in `.research/evaluation.json`;
   `make list-tasks` shows what each task type returns). On contract
   errors, `make validate-inputs RUN_ID=<run_id>` pinpoints them
   without scoring. The report includes `metrics`, `curves`, `skipped`
   (uncomputable metrics with reasons — report these, never fill them
   in yourself) and `provenance`. Commit the evaluation outputs.
2. **Read the results**: `fetch_experiment_results` (reads the
   repository).
3. **Author the analysis** via
   `get_generation_prompt("experiment_analysis", ...)`, passing the
   experiment code from the clone as
   `{"files": {"<path>": "<content>"}}`. Write it in Japanese. Report
   what the numbers show, including when they do not show what was
   hoped — the analysis is evidence, not advocacy.
4. **Result charts**: build a Vega-Lite spec and `render_chart` it
   (pass the clone as `local_path`) to
   `.research/results/chart/<name>.png` — PNG, not PDF. Data numbers
   must be metric references (`"metric:run_1.accuracy"`), never
   literals: the tool resolves them from `.research/results/` itself,
   so a plotted point cannot be invented. The tool appends the chart's
   spec to `.research/record.json` as its declaration and commits both
   in the same step — verification re-renders every chart from its
   declared spec and fails on differences or undeclared chart files.
5. **Method diagrams**: write text notation (mermaid / graphviz / d2)
   and `render_diagram` to `.research/results/diagram/<name>.pdf`.
6. Commit and push. Reference figures in LaTeX as `images/<path>` with
   the full relative path you were given — two runs can each produce
   `accuracy.pdf`, and only the full path resolves.

**Output**: an analysis in `.research/research_history.json` and
committed, verifiable figures.
