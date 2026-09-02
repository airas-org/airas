---
name: publish-paper
description: Take a frozen AIRAS paper from experiment results to the paper of record — realize every stated number from declared values, compile and verify locally until green, then push and let CI re-run the verification, handing the user the CI-built PDF artifact and report. Use after experiments to fill, check, and publish the paper, or just to check whether the numbers hold up (stop before pushing).
---

# Publish the paper

Needs a main.tex and results with their provenance manifest in a
clone. Two stages with two checkpoints: **local green** (your own
check) and **CI green** (the check outside your hands — only its
artifact is the paper of record). A red CI gate loops back to the
local stage.

## Local: realize and verify until green

1. **Realize the numbers from declarations.** One `compute_paper_values`
   declaration per value the paper states, e.g. `{"key": "acc_gain",
   "op": "pct_improve", "refs": ["proposed.accuracy",
   "baseline.accuracy"], "round": 1}`. The tool reads
   `.research/results/` itself — numbers cannot be passed in — and
   writes `values.json` + `values.tex` into `.research/latex/{template}/`.
   This is the only sanctioned way an experimental number enters the
   paper. Tables likewise: never hand-write a tabular of experimental
   numbers — declare each to `compute_paper_tables` and
   `\input{tables/<key>.tex}` (cells are always
   `<row.run_id>.<column.ref_path>`, so a label cannot be paired with
   another run's number). If the repository contains a preregistered
   main.tex, realize its declaration comment block verbatim and honor
   the `preregister-paper` contract: claims are append-only, and a
   failed criterion is reported as a negative result, not rewritten.
   Need an undeclared value? Extend the declarations and re-run —
   never type the number. A number no declaration can produce (e.g.
   quoted from a cited paper) must be wrapped as `\unverified{...}`.
   Bibliography: `generate_bibfile` →
   `.research/latex/{template}/references.bib`.

2. **Verify**: `verify_latex` with `local_path` (working tree; no
   push, no keys). It compiles and reports `ok`, `page_count`,
   `undefined_citations`, `undefined_references`, `missing_figures`,
   and — when `values.json` exists — recomputes every value from the
   run outputs, diffs `values.tex` against a regeneration, requires
   every `\airasval` key to be defined, regenerates declared tables
   and charts, and cross-checks local metrics against the run declared
   in `.research/results/.provenance.json` (byte-identical, commit an
   ancestor of HEAD). Loop with step 1 until `ok` — a `?` citation
   and an absent figure still produce a PDF, and a value failure
   suppresses it outright.

3. **Report what the verification says, not just that it passed**:
   `provenance.status == "unavailable"` — say so rather than
   presenting the numbers as provenance-backed; `sibling_run_ids` —
   the same code ran more than once, name the run the paper reports;
   `\unverified{...}` occurrences — surface them for human review.

If the user only asked whether the numbers hold up, stop here and
commit the realized files; publishing is the outward step below.

## Official: CI verifies, its artifact is the record

4. **Push** the final state. The template's verification workflow
   re-runs the full gate (value recomputation, provenance cross-check,
   compile) and, only when everything passes, uploads the PDF and the
   verification report as the workflow's artifacts.

5. **Confirm the gate is green** (`get_workflow_runs`) and give the
   user the commit sha, the workflow-run URL, and the artifact — that
   trio is the citable, re-checkable result. A red gate is not
   published: return to the local stage, fix, push again.

6. **Persist**: `upload_research_history`, so a later session can
   restore with `download_research_history`.

7. **Optional, on request — editable export**: `open_in_overleaf`
   (pass `local_path` to export without pushing). Say explicitly that
   this copy is **outside the verification guarantee**: editable,
   never read back, not covered by the CI-verified artifact. Each
   click creates a new project.

**Output**: a green verification run whose CI-built PDF and report the
user has been handed, plus persisted research state.
