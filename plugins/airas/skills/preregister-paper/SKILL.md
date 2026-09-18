---
name: preregister-paper
description: Write the preregistration paper (prereg main.tex) for a research repository whose hypothesis and experimental design already exist, before any experiment has run. Hypothesis, predictions and design are written in full as numbered claims with criteria and predicted intervals; Results and Discussion stay stubs until experiments fill them, and every experimental number is an \airasval placeholder. Use when the user wants the paper declared before experiments (the AIRAS integrity flow), asks for a prereg PDF, or says 事前登録 / preregister / "write the paper first".
---

# Preregister the paper

You write the paper **before** the experiments, from the hypothesis and
experimental design alone. The commit that adds this paper is the
preregistration record: every claim, criterion and expected result is
frozen in git history before any result exists, so nothing can be
quietly rewritten to fit the data later. Runs are expected to descend
from this commit.

main.tex lives in `.research/latex/{template}/`, where `{template}` is
one of the bundled template directories (`iclr2024`, `mdpi`,
`agents4science_2025`) — the name the verification tools address the
paper by. The directory is only a slot: use the bundled style or your
own preamble, keeping the usual structure (title, abstract, numbered
sections, figures, bibliography). Write in the user's working
language; a CJK paper needs a LuaTeX preamble (`luatexja-fontspec` —
pdflatex silently drops non-Latin text from the PDF), and with the `mdpi`
class also `\RequirePackage{luatex85}` before `\documentclass` (drop its
`pdftex` option), since the class uses pdfTeX primitives LuaTeX no longer
has. This skill only changes *when* the paper is written and how Results
are stated.

## Preconditions

- A local clone of the experiment repository.
- Hypothesis and experimental design exist, from
  `hypothesize-and-design` or supplied by the user. The design must fix
  the run ids (e.g. `proposed`, `baseline`) and the metrics; if it does
  not, settle those with the user first, because the placeholders below
  are named after them.
- The papers the hypothesis rests on, each with its identifiers, the
  `fulltext_path` `fetch_paper_fulltext` wrote, and the passages (page
  and verbatim quote) picked while reading. Nothing is in the record yet.

## Steps

1. **Create the canonical record with `preregister_record`**, passing
   the `literature` and the `hypotheses` together. This writes
   `.research/record.json` — the machine-readable original the whole
   verification system keys on — and pins each source: a registry
   (doi.org, arXiv, git) confirms it exists, its full text is
   copied to `.research/sources/<id>/fulltext.txt`, and every quote is
   checked against that snapshot. `literature` entries are papers
   (`doi` / `arxiv_id` with `title`, `authors`, `year`,
   `venue`, `pdf_url`, `fulltext_path`), repositories (`url`, a full
   40-hex `commit`, `files`) or studies AIRAS produced (`airas_record`),
   each with `passages: [{"node_type": ..., "quote": "<verbatim>"}]`.
   A quote that the snapshot does not contain (line breaks, hyphenation
   and ligatures are normalised away; a paraphrase or a quote spanning
   two pages is not) makes the call fail and roll back, so nothing is
   frozen until every quote is found — and CI runs the same check on
   the pushed commit.
   Sources are numbered in the order given (`s1`, `s2`, …) and passages
   `p1`, `p2`, … within each. The record is a tree, read as
   "to support this hypothesis, these claims; to verify this claim,
   these designs; a design is these runs":

   ```
   hypotheses: [{
     "id": "h1", "statement": "the hypothesis, in prose",
     "grounded_on": ["s1.p2", ...],
     "assumptions": ["what must be granted for the claims together to
                      imply h1, naming the claims concerned", ...],
     "claims": [{
       "id": "c1", "statement": "one assertive sentence",
       "rationale": "why c1 holding is evidence for h1, and for which part",
       "cites_passages": ["s1.p2", ...],
       "verifier": {"kind": "seyval"},
       "criterion": {"metric": "accuracy", "subject": "proposed-...",
                     "reference": "comparative-1-...", "op": ">=",
                     "margin": 0.02},
       "prediction": {"low": 0.02, "high": 0.04, "basis": "pilot run"},
       "designs": [{
         "id": "d1", "summary": "...",
         "runs": [{"run_id": "proposed-...", "description": "...",
                   "params": {"mode": "full"}}]
       }]
     }],
     "tables": [...], "notes": [...]
   }]
   ```

   `notes` (free text on the hypothesis) holds what the fields above
   cannot: the gap in prose, why each margin and interval was chosen, the
   compute target. It is frozen with the record and is where a fresh
   session reads the design rationale from.

   `grounded_on` and `cites_passages` (also on designs and runs, and
   `reference_passage` on a criterion whose `reference` is a constant
   read from a paper) name those passages as `s1.p2` — the prior work's
   own words the declaration rests on. The gate refuses a passage no
   source declares.

   `run_id` names the results directory the run will produce and must be
   unique across the record — a run belongs to exactly one claim, and
   results for an undeclared run_id fail verification. `params` declares
   only what the commit *cannot* fix: the conditions the dispatch will
   apply. Everything else (batch size, seeds, dataset) already lives in
   the repository's config files, which the commit freezes. Declaring
   the params is what makes "we said full and ran pilot" detectable
   later — the gate compares them with what the platform recorded.

   `criterion` is the falsification line, required for every seyval
   claim: `(subject.metric - reference) op margin`, where `reference` is
   another run under the claim (its same metric) or a constant. The
   verdict — supported or refuted — is derived from it once the runs are
   in, and it is frozen with the claim: moving the margin later fails
   the gate like rewording the statement. `prediction` is the interval
   the difference is expected to land in, required, a range never a
   point, with where it comes from. Whether the claim was declared
   before its runs executed is not modelled yet (TODO). A second
   hypothesis is a second entry in `hypotheses`.

   A claim proved in Lean has `"verifier": {"kind": "lean", "toolchain":
   ..., "mathlib_rev": ..., "allowed_axioms": [...]}` — the toolchain and
   mathlib revision are the repository's `lean/lean-toolchain` and
   `lean/lake-manifest.json` — and no criterion or prediction; its run's
   `params` are `{"module": ..., "decl": ..., "statement": ...}`, the
   statement being what `#check @decl` prints. The statement is what gets
   frozen: the proof is written afterwards, and a built declaration whose
   type differs from it is inconclusive. See `_shared/references/lean.md`.

   The claims are meant to imply the hypothesis together: c1 ∧ … ∧ cn
   ⇒ h1. `rationale` (required on every claim) says why the claim is a
   member of that set — which part of the hypothesis it carries and why
   its holding is evidence for it. `assumptions` (on the hypothesis)
   say what has to be granted for the conjunction to reach h1: that the
   metric stands for the property, that the datasets run generalise,
   that the baseline is representative, and so on, each naming the
   claims it concerns. These are exactly what every claim being
   supported still leaves unverified, so state them as assumptions, not
   as findings; an assumption that can be turned into a measurement is
   a missing claim.

   The tool also writes `claims.tex` — the numbered claim list with each
   criterion, prediction and (pending) verdict — and `references.bib`
   next to main.tex, and commits them with the record and the source
   snapshots as the one freeze commit.

2. **Write `.research/latex/{template}/main.tex`** against
   `get_prompts(step="paper_writing")`. It states the rules the gate
   holds the paper to (the hypothesis, claims, bibkeys and passages are
   in record.json and claims.tex): the frozen part written in
   full now and the post-experiment part left as stubs behind the marker
   comment, `\input{claims.tex}` for the hypothesis and predictions,
   `\airasval` for every experimental number (none appears before the
   marker), `\cite[s1.p2]{key}` for a sentence resting on a passage, the
   fallback preamble that compiles without values.tex, and the LuaTeX
   notes for a CJK paper.

3. **Compile until green — this is a freeze condition, not a
   courtesy check.** Run `verify_latex` with `local_path` and iterate
   until `ok`; any `\airasval` rendering as `??airasval:key??` is the
   correct prereg state, not an error. A paper that does not
   compile must not be frozen: post-experiment "fixes to make it
   compile" open an editing channel where narrative changes can hide.
   The local build is only the fast feedback loop — the local
   toolchain is in the agent's hands, so its PDF proves nothing. The
   **official prereg PDF is the CI artifact**: once the freeze commit
   passes `Verify Record` on the staging ref and is fast-forwarded onto
   the protected branch, `Publish Paper` builds it there, where the
   agent cannot interfere, and that artifact is what a human
   reviews at freeze time (are the criteria reasonable? are the
   intervals narrow enough to miss? are the claims falsifiable?) and
   what a reader compares the final paper against.

4. **Commit main.tex and push.** `preregister_record` already committed
   record.json and returned the `freeze_commit` sha — that commit is the
   freeze point. Commit the prereg main.tex on top, push, and tell the
   user the freeze sha — later verification argues from runs being
   descendants of it.

   **Once committed, the record only ever grows**: every later revision
   must *contain* the committed one whole, so the verifier fails on a
   reworded claim, a changed run condition, a reordered list or a
   dropped result alike — it does not have to enumerate what may change. The
   legitimate revision path is `append_to_record`: append an entry with
   the **same id**, and the later one becomes the live version while the
   earlier stays readable in place. To retire an entry with no
   replacement, append it again with `"withdrawn": true`. A claim becomes
   **verified** when every run under it has results — the data it rests
   on is in. `verified` does not say the claim held, and (for now) not
   that it was declared before its runs executed; both are TODO. Once
   results
   exist, the legitimate diff to main.tex is what the results force
   (values realized, negative results discussed) — a compiling freeze
   keeps that diff small enough to review.

## After the experiments

Results and Discussion are written now, in the stub region; the same
`get_prompts(step="paper_writing")` states the rules for this stage. Do not edit the claims to fit the
results. The honest paths are:

- A criterion that fails is a **negative result**: keep the claim,
  report that it did not hold, and discuss why. A value that meets the
  criterion but misses the interval is reported as such, not hidden.
- A new finding is a **new claim** with its own design and runs,
  appended via `append_to_record` under its hypothesis, and presented
  as exploratory. Dispatch its confirmation run after the append is
  committed; the record cannot yet tell a preregistered claim from a
  post-hoc one, so the discipline is yours.
- Realize the record's declarations with `update_record` (it reads
  record.json and the run outputs itself, and commits what it wrote;
  the verdict on it comes from CI, not from the tool); if you need a
  number you did not declare, append the declaration with
  `append_to_record` — never type it.
