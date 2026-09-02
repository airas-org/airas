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

1. **Create the canonical record with `preregister_record`.** This
   writes `.research/record.json` — the machine-readable original the
   whole verification system keys on. Pass the hypothesis and design
   prose, every planned run (`runs`; results for an undeclared run_id
   fail verification later), the numbered claims (`claims`: id `c1`...,
   statement, prose criterion, predicted interval, the run_ids that
   test it), and for every experimental number the paper will state its
   value declaration up front, e.g.
   `{"key": "improvement_pct", "op": "pct_improve", "refs":
   ["proposed.accuracy", "baseline.accuracy"], "round": 1}` — refs
   address the planned run ids, the same ids the experiment code will
   be held to. Table specs can be declared here too.

2. **Write `.research/latex/{template}/main.tex` in two parts.**
   The *frozen part* — title, abstract, introduction, related work,
   **hypothesis and predictions**, method, experimental design — is
   written in full now. The *post-experiment part* — Results and
   Discussion — is left as stubs behind a marker comment
   (`% ===== airas: post-experiment sections, filled once runs exist =====`),
   so the diff at publish time is confined to a region a reviewer can
   find.

   The **hypothesis and predictions section is a numbered list of
   claims** (C1, C2, ... — the same ids as in record.json, which is the
   canonical form; the paper prose is its human rendering). Each claim
   is one assertive sentence plus,
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
   `values.tex` cannot exist yet (update_and_verify_record needs run
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

   Once experiments run and `update_and_verify_record` writes `values.tex`,
   the same main.tex picks up the real numbers with no edit.

4. **Compile until green — this is a freeze condition, not a
   courtesy check.** Run `verify_latex` with `local_path` and iterate
   until `ok`; any `\airasval` rendering as `??airasval:key??` is the
   correct prereg state, not an error. A paper that does not
   compile must not be frozen: post-experiment "fixes to make it
   compile" open an editing channel where narrative changes can hide.
   The local build is only the fast feedback loop — the local
   toolchain is in the agent's hands, so its PDF proves nothing. The
   **official prereg PDF is the CI artifact**: the freeze push triggers
   `verify_paper.yml`, which re-verifies the record and rebuilds where
   the agent cannot interfere, and that artifact is what a human
   reviews at freeze time (are the criteria reasonable? are the
   intervals narrow enough to miss? are the claims falsifiable?) and
   what a reader compares the final paper against.

5. **Commit main.tex and push.** `preregister_record` already committed
   record.json and returned the `freeze_commit` sha — that commit is the
   freeze point. Commit the prereg main.tex on top, push, and tell the
   user the freeze sha — later verification argues from runs being
   descendants of it.

   **Once committed, the record's declarations are immutable**: the
   verifier walks record.json's git history and any edit to an existing
   entry (or to the hypothesis/design prose) fails verification. The
   legitimate revision path is `append_to_record` — append a new entry
   whose `supersedes` names the old id; the old entry stays in the
   file, visibly, and is no longer realized. A claim becomes
   **verified** only when its runs executed a commit that already
   contained the identical claim, so a declaration added after the run
   stays unverified forever — that is the whole point. Once results
   exist, the legitimate diff to main.tex is what the results force
   (values realized, negative results discussed) — a compiling freeze
   keeps that diff small enough to review.

## After the experiments

Results and Discussion are written now, in the stub region: every
claim reported by number against its criterion and predicted interval.
Do not edit the claims to fit the results. The honest paths are:

- A criterion that fails is a **negative result**: keep the claim,
  report that it did not hold, and discuss why. A value that meets the
  criterion but misses the interval is reported as such, not hidden.
- A new finding is a **new claim**, appended via `append_to_record` and
  presented as exploratory unless a fresh confirmation run (dispatched
  after the append is committed) supports it — only then can its
  verified flag ever go true.
- Realize the record's declarations with `update_and_verify_record` (it
  reads record.json itself and verifies what it wrote in the same
  step); if you need a number you did not declare, append the
  declaration with `append_to_record` — never type it.
