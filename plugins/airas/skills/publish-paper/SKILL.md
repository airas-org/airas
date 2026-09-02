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

1. **Realize the record from the run outputs.** The declarations live
   in `.research/record.json` (created at preregistration);
   `update_and_verify_record` reads them and `.research/results/`
   itself — numbers cannot be passed in — writes into record.json each
   run's measured metrics with its execution trail, the computed
   values, and the per-claim verified flags, renders `values.tex` and
   `tables/<key>.tex` into `.research/latex/{template}/` (each
   `\airasval` prints as a hyperlink to record.json on the repository's
   origin; table cells are always `<row.run_id>.<column.ref_path>`, so
   a label cannot be paired with another run's number), and **then
   verifies everything it wrote in the same step**, returning the
   verification report — a `verified: true` in the record is backed the
   moment it is written. This is the only sanctioned way an
   experimental number enters the paper; never hand-write a tabular of
   experimental numbers. Honor the `preregister-paper` contract: the
   record is append-only, and a failed criterion is reported as a
   negative result, not rewritten. Need an undeclared value? Append the
   declaration with `append_to_record` and re-run — never type the
   number. A number no declaration can produce (e.g. quoted from a
   cited paper) must be wrapped as `\unverified{...}`.
   Bibliography: `generate_bibfile` →
   `.research/latex/{template}/references.bib`.

2. **Verify**: `verify_latex` with `local_path` (working tree; no
   push, no keys). It compiles and reports `ok`, `page_count`,
   `undefined_citations`, `undefined_references`, `missing_figures`,
   and — when `record.json` exists — recomputes every value from the
   run outputs, diffs `values.tex` against a regeneration, requires
   every `\airasval` key to be declared, regenerates declared tables
   and charts, checks the record's git history is append-only, rejects
   results directories no declared run accounts for, recomputes each
   claim's verified flag, and cross-checks local metrics against the
   run declared in `.research/results/.provenance.json`
   (byte-identical, commit an ancestor of HEAD). Loop with step 1 until
   `ok` — a `?` citation and an absent figure still produce a PDF, and
   a value failure suppresses it outright.

3. **Report what the verification says, not just that it passed**:
   `provenance.status == "unavailable"` — say so rather than
   presenting the numbers as provenance-backed; `sibling_run_ids` —
   the same code ran more than once, name the run the paper reports;
   `\unverified{...}` occurrences — surface them for human review;
   `unverified_claims` — claims whose declared runs never executed (or
   executed a commit that lacked the declaration) may still be
   published, but say so honestly in the paper and to the user.

If the user only asked whether the numbers hold up, stop here — the
realized files are already committed by `update_and_verify_record`;
publishing is the outward step below.

## Official: CI verifies, its artifact is the record

4. **Commit the main.tex edits and push** the final state. The template's verification workflow
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
