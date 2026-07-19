---
name: results-for-paper-writing
description: Structure experiment outputs so analysis and paper generation can consume them — machine-readable metrics, baselines on equal footing, honest comparisons.
category: results_and_analysis
tags: [results, metrics, analysis, paper-writing, baselines]
sources:
  - https://github.com/airas-org/airas-template
updated: "2026-07-19"
---

# Results that survive the pipeline

In AIRAS the consumer of experiment results is not a human reading logs but
`analyze_experiment` and `generate_paper`. Numbers that exist only in stdout
or a W&B dashboard effectively do not exist. Design the output files first,
then the code that fills them.

## Output contract

- **One machine-readable results file per run** (JSON/CSV at the template's
  contracted path) containing: every metric named in the experimental
  design's `primary_metric`/secondary metrics, the condition (method,
  hyperparameters), the seed, and dataset sizes. Include units and
  higher-is-better direction if ambiguous.
- **Keep per-seed rows, not just aggregates.** The analysis step should be
  able to recompute mean ± std and run significance checks; pre-aggregated
  single numbers destroy that option.
- **Write results incrementally** (after each condition/seed), so a job
  killed at the time limit still yields the completed conditions.
- **Figures are generated from the results files**, never from numbers
  retyped into plotting code — retyping is where transcription errors enter
  papers.

## Baselines on equal footing

- Baselines run in the **same pipeline, same data split, same seeds, same
  budget** as the proposed method. A baseline number copied from a paper is
  a different experiment; if quoted anyway, mark it as reported-elsewhere in
  the results file so the paper can attribute it honestly.
- Tune the baseline with the same effort policy as the proposed method
  (e.g. same search budget). An untuned baseline is the most common way
  automated pipelines manufacture fake wins.
- Include a **trivial baseline** (majority class, random, zero-shot) — it
  catches evaluation bugs: if the fancy method barely beats random, either
  the method or the metric implementation is broken.

## Honest reporting rules

- Report **all conditions that ran**, not the best subset; if a run failed,
  record it as failed rather than dropping the row.
- Fix metric definitions before looking at results (which split, which
  aggregation, which decimals) — post-hoc metric selection is p-hacking by
  another name, and an automated loop will do it silently if allowed.
- When a difference is within one standard deviation across seeds, the
  results file should say so plainly; the paper-writing step will otherwise
  narrate noise as a finding.
