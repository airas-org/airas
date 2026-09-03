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

## Local: realize the record and write the paper

1. **Realize the record from the run outputs.** The declarations live
   in `.research/record.json` (created at preregistration);
   `update_record` reads them and `.research/results/`
   itself — numbers cannot be passed in — appends to each run a
   result (the platform's execution id and commit, the hash of the
   evaluation inputs, the evaluator's report, and the metrics file
   verbatim), marks each claim all of whose runs have results as
   `verified`, renders `values.tex` and
   `tables/<key>.tex` into `.research/latex/{template}/` (each
   `\airasval` prints as a hyperlink pinned to the commit that wrote the
   record; table cells are always `<row.run_id>.<column.ref_path>`, so
   a label cannot be paired with another run's number), and commits
   what it wrote. It does **not** judge the result: a local verdict
   could be pushed past regardless, so the judgement is CI's, on the
   pushed commit. This is the only sanctioned way an experimental
   number enters the paper; never hand-write a tabular of experimental
   numbers. Honor the `preregister-paper` contract: the
   record is append-only, and a claim that missed its criterion is
   reported as a negative result, not rewritten.

   **Run `update_record` last, after every other change to the
   record.** The links in `values.tex` pin the commit that last wrote
   `record.json`, and the gate regenerates `values.tex` from that
   commit — so a `render_chart` or `append_to_record` made *after*
   `update_record` leaves `values.tex` pointing at a superseded commit
   and the gate reports `values.tex differs from its regeneration`.
   The tool is idempotent (a result already recorded is not appended
   twice), so re-running it after a late chart or append is the fix.

   `\airasval` addresses one of two things, both writable before any
   run exists:

   | Form | Prints |
   | --- | --- |
   | `<run_id>.<metric.path>` | a metric of a declared run, read from its metrics file |
   | `<run_id>.params.<key>` | a condition the run was declared with |

   The `params` form reads the declaration; the gate checks that
   declaration against what the platform recorded for the dispatch, so
   citing a batch size cites a condition the run was held to. Derived
   numbers (a claim's target) are not modelled yet. Need an undeclared value? Append the
   declaration with `append_to_record` and re-run — never type the
   number. A number no declaration can produce (e.g. quoted from a
   cited paper) must be wrapped as `\unverified{...}`.
   Bibliography: `generate_bibfile` →
   `.research/latex/{template}/references.bib`.

2. **Check that it builds**: `verify_latex` with `local_path`
   (working tree; no push). Use it for what a local run can honestly
   tell you — whether the document compiles, and `page_count`,
   `undefined_citations`, `undefined_references`, `missing_figures`.
   Loop with step 1 until it compiles cleanly; a `?` citation and an
   absent figure still produce a PDF, so read the fields rather than
   the presence of the file.

   It also re-runs the record checks, and those are worth reading when
   something looks wrong — but they are **diagnostics, not a verdict**.
   A green local run proves only that the agent's own toolchain agrees
   with itself. Do not report a paper as verified on this basis, and do
   not treat a local pass as permission to skip reading the CI run.

3. **Report what CI's verification says, not just that it passed.**
   Once the gate has run (step 5), read its report rather than the
   local one:
   `provenance.status == "unavailable"` — say so rather than
   presenting the numbers as provenance-backed; `sibling_run_ids` —
   the same code ran more than once, name the run the paper reports;
   `\unverified{...}` occurrences — surface them for human review;
   `unverified_claims` — claims some of whose declared runs have no
   results may still be published, but say so honestly in the paper and
   to the user. `verified: true` says the claim's data is in, not that
   it held: a claim that was tested and missed the criterion stated in
   the paper is a **negative result**, reported as such. Never read the
   verified flags alone as support for the hypothesis, and never reword
   a claim to fit what the data did.

Even if the user only asked whether the numbers hold up, the answer
comes from CI: the realized files are already committed by
`update_record`, so push and read the gate. There is no local
shortcut that settles the question.

## Official: CI verifies, its artifact is the record

4. **Commit the main.tex edits and push to the staging ref** — not to
   the protected branch (`git push origin main:verify`). The required
   check, `Verify Record`, runs there. It is the whole integrity
   verdict: the record's checks (recomputation, containment history,
   provenance cross-check) **and the paper's numbers** — values.tex
   against its regeneration, declared tables, every `\airasval` key
   declared. None of that needs LaTeX, so it is fast, and a
   hand-edited number is caught here, before the sha can land. The
   report is uploaded even when red, so a failure is readable rather
   than merely reported.

5. **Confirm the gate is green** — `get_workflow_runs` with
   `branch_name="verify"`, reading the run whose `head_sha` is the sha
   you pushed (an older green run on the same ref proves nothing about
   the new commit) — then
   fast-forward the same sha onto the protected branch
   (`git push origin main:main`) — **never squash or rebase**. Squash and rebase rewrite commits, and verification asks
   whether each run's recorded commit is an ancestor of HEAD; after a
   rewrite it is not, so the merge that was supposed to publish the
   result is what invalidates it. A fast-forward lands the exact sha
   CI judged. (`prepare_repository` disables both merge methods, so
   normally the attempt simply fails — do not work around it.)

   Landing on the protected branch is what publishes. `Publish
   Paper` runs there and nowhere else — every sha on that branch has
   already passed the gate, so all that is left is to compile and
   upload the PDF with its report. That ordering comes from the
   branch rule, not from one workflow waiting on another.

   Give the user the commit sha, the `Publish Paper` run URL, and
   its artifact — that trio is the citable, re-checkable result. A
   red gate is not published: return to the local stage, fix, push
   to the staging ref again. A red *publish* on a green gate is a
   rendering failure (a citation, a figure), not an integrity one;
   fix it the same way.

6. **Persist**: `upload_research_history`, so a later session can
   restore with `download_research_history`.

7. **Optional, on request — editable export**: `open_in_overleaf`
   (pass `local_path` to export without pushing). Say explicitly that
   this copy is **outside the verification guarantee**: editable,
   never read back, not covered by the CI-verified artifact. Each
   click creates a new project.

**Output**: a green verification run whose CI-built PDF and report the
user has been handed, plus persisted research state.
