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
pdflatex silently drops non-Latin text from the PDF). This skill only
changes *when* the paper is written and how Results are stated.

## Preconditions

- A local clone of the experiment repository.
- Hypothesis and experimental design exist — in
  `.research/research_history.json`, or supplied by the user. The
  design must fix the run ids (e.g. `proposed`, `baseline`) and the
  metrics; if it does not, settle those with the user first, because
  the placeholders below are named after them.

## Steps

1. **Pick value keys now.** For every experimental number the paper
   will state, decide its key and derivation up front, e.g.
   `improvement_pct = pct_improve(proposed.accuracy, baseline.accuracy)`.
   Refs address the planned run ids — the same ids the experiment code
   will be held to. Record the full list in a comment block at the top
   of main.tex:

   ```latex
   % airas prereg declarations (compute_paper_values will realize these):
   %   improvement_pct = pct_improve(proposed.accuracy, baseline.accuracy) round 1
   ```

2. **Write `.research/latex/{template}/main.tex` in two parts.**
   The *frozen part* — title, abstract, introduction, related work,
   **hypothesis and predictions**, method, experimental design — is
   written in full now. The *post-experiment part* — Results and
   Discussion — is left as stubs behind a marker comment
   (`% ===== airas: post-experiment sections, filled once runs exist =====`),
   so the diff at publish time is confined to a region a reviewer can
   find.

   The **hypothesis and predictions section is a numbered list of
   claims** (C1, C2, ...). Each claim is one assertive sentence plus,
   in prose: the criterion (the threshold on a declared value key that
   counts as support — below it the claim is refuted) and the
   **predicted interval** — a range, never a point ("we predict an
   improvement of 2–4 points"), with where the range comes from (prior
   work, pilot). The criterion is the falsification line, the interval
   is what you expect; an outcome outside the interval in either
   direction must be discussed later. A range too wide to miss is a
   criterion, not a prediction. Every experimental number is
   `\airasval{key}` and appears only in the post-experiment part —
   never a literal, not even an expected one presented as measured.

3. **Make it compile without values.tex.** The tool-generated
   `values.tex` cannot exist yet (compute_paper_values needs run
   metrics), so the preamble must provide the same fallback it would:

   ```latex
   \InputIfFileExists{values.tex}{}{}
   \providecommand{\airasval}[1]{\textbf{??airasval:\detokenize{#1}??}}
   \providecommand{\unverified}[1]{#1}
   ```

   (`\providecommand` is a no-op once values.tex defines the macros.
   Do not move these definitions into an `\IfFileExists` branch — a
   macro body with `#1` inside another macro's argument does not
   compile.)

   Once experiments run and `compute_paper_values` writes `values.tex`,
   the same main.tex picks up the real numbers with no edit.

4. **Compile until green — this is a freeze condition, not a
   courtesy check.** Run `verify_latex` with `local_path` and iterate
   until `ok`; any `\airasval` rendering as `??airasval:key??` is the
   correct prereg state, not an error. A paper that does not
   compile must not be frozen: post-experiment "fixes to make it
   compile" open an editing channel where narrative changes can hide,
   and the compiled prereg PDF is what a human reviews at freeze time
   (are the criteria reasonable? are the intervals narrow enough to
   miss? are the claims falsifiable?). Keep
   the PDF — it is the preregistration record a reader compares the
   final paper against.

5. **Commit and push.** This is the freeze point. Say so in the commit
   message (e.g. `prereg: declare paper before experiments`). Tell the
   user the commit sha — later verification argues from runs being
   descendants of it.

   The freeze binds declarations to *results*, not to the calendar:
   **until an experiment has run, revising the hypothesis and
   re-preregistering is legitimate science, not a violation** — run
   this skill again and the freeze point simply moves (the old
   version stays in history for transparency). What the freeze
   forbids is only claiming a run as support for a declaration that
   did not yet exist when that run executed. Once results exist, the
   legitimate diff to main.tex is what the results force (values
   realized, negative results discussed) — a compiling freeze keeps
   that diff small enough to review.

## After the experiments

Results and Discussion are written now, in the stub region: every
claim reported by number against its criterion and predicted interval.
Do not edit the claims to fit the results. The honest paths are:

- A criterion that fails is a **negative result**: keep the claim,
  report that it did not hold, and discuss why. A value that meets the
  criterion but misses the interval is reported as such, not hidden.
- A new finding is a **new claim**, added after the fact and presented
  as exploratory unless a fresh confirmation run (dispatched after the
  addition) supports it.
- Realize the declarations from step 1 verbatim with
  `compute_paper_values`; if you need a number you did not declare,
  extend the declarations — never type it.
