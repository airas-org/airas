---
name: auto-research
description: End-to-end automated research with the AIRAS integrity flow — the paper is preregistered (claims, criteria and expected results frozen in git) before any experiment runs, and every reported number is realized and verified from run outputs afterwards. This skill holds only the ordering and the rules that span steps; each step's contract lives in its own skill. Use when the user wants to run an AIRAS research project start to finish, or asks where in the flow they are or what comes next.
---

# AIRAS research orchestrator

This file owns the **order** and the **invariants**; nothing else.
Each step's how-to lives in its own skill — invoke it on entering the
step and follow it over anything more generic. The steps themselves
are deliberately independent: they state what repository state they
need and what they leave behind, and only this file says which comes
after which.

## Flow

Run these skills in order:

- `setup-repository` — experiment repo created and cloned
- `discover-papers` — literature into a study list
- `hypothesize-and-design` — falsifiable hypothesis; run ids and
  metrics settled; research context committed
- `preregister-paper` — the full paper written and committed **before
  any experiment**; this commit is the freeze point
- `write-experiment-code` — code to the execution and airas-eval
  contracts, environment fixed by lockfile + Dockerfile
- `run-experiments` — execute on the platform, bring results back
  with provenance
- `analyze-results` — analysis and verifiable figures
- `publish-paper` — numbers realized from declarations, compile +
  recompute + provenance checks until green locally, then push: CI
  re-runs the verification and its artifact — the paper of record —
  is handed to the user, state persisted

Execution platform references live in `_shared/references/` per
platform.

## Settle once, up front

Operational choices otherwise surface one tool default at a time,
mid-flow. Ask the user for them together before starting the flow and
carry the answers through the session:

- repository visibility — `prepare_repository` defaults to **private**
- execution platform; for Seyval, managed vs **BYO** compute and, when
  several exist, which workspace
- compute target (GPU and architecture) — the experimental design and
  the dependency lockfile depend on it

## Invariants across steps

These are the orchestrator's own rules; no step may relax them.

- **Nothing is dispatched before the freeze commit exists.**
  `run-experiments` must not start until `preregister-paper` has
  committed. Carry the freeze commit sha through the session and
  report it to the user; verification argues from runs being
  descendants of it.
- **Runs descend from the freeze commit.** Fixes are committed on top
  of it, never instead of it — no amending or rebasing away the
  prereg commit.
- **The record only ever grows.** `.research/record.json` holds the
  hypothesis, its designs, their runs and the claims. Every committed
  revision must *contain* the one before it whole, so a reworded claim,
  a loosened criterion, a reordered list and a dropped execution all
  fail the same check. Revision is an append with the **same id** (the
  later entry is the live one, the earlier stays readable); retirement
  is an append with `"withdrawn": true`. Re-running an experiment
  appends an execution rather than replacing one, so "we ran it three
  times" stays in the record and which execution the paper reports is
  itself recorded. A claim that fails is reported as a negative result,
  not deleted or reworded into something the data supports; new
  findings enter as new, explicitly exploratory claims declared and
  committed *before* their confirmation run — a claim only ever
  verifies against a run whose commit already contained it.
- **No experimental number is ever typed.** Numbers reach the paper
  only as `\airasval{...}` — a claim's target, a run's metric, or a
  parameter the run actually executed with — and through declared
  tables and charts; anything else is `\unverified{...}` and said to
  the user. This covers the experimental setup too, not just results:
  a stated batch size the run never used is the same defect as a
  fabricated accuracy.
- **State handoff is the repository.** Everything a later step needs
  must be committed, not held in conversation — a fresh session must
  be able to resume from the clone alone.

## The integrity model — why the gate holds

Two rules generate every check; reason from them when a situation the
steps don't cover comes up.

1. The agent authors only *declarations* (append-only, revision = a
   later entry with the same id) and prose. Every number, result and
   verified flag in record.json is machine-derived.
2. Anything machine-derived must equal its re-derivation at
   verification time. Nothing is trusted for *who* wrote or committed
   it — content is judged, authorship is not.

`verified` is therefore never set, only derived: the claim's runs have
results ∧ each run's commit is an ancestor of HEAD ∧ that commit
already contained the identical declarations. A hand-set flag simply
differs from its re-derivation and fails.

**`verified` is not `criterion_met`.** The first says the claim was
properly preregistered and tested; the second says the measured value
fell inside the frozen criterion. They are recorded separately because
a refuted claim is verified and unmet — that is a result, not a
failure of the record. Reading a column of `verified: true` as "the
hypothesis held" is the misreading the second field exists to
prevent.

Trust domains: local runs of the checks (including the one inside
`update_and_verify_record`) are fast feedback with **zero evidentiary
value** — the local toolchain is in the agent's hands. The judgement
is the CI run on the pushed history, anchored by two stores the agent
cannot write: Seyval's run records (execution id, commit hash, output
bytes) and git's content-addressed history. Consequences: rewriting a
committed declaration turns the branch permanently red (the history
walk sees every version); forged numbers, metrics or flags fail
recomputation or the Seyval byte-comparison; rewriting history after
a run detaches the run's commit from HEAD and voids the results
themselves. Before any run exists, redoing the record is legitimate —
nothing is anchored yet, so nothing can be hidden.

## Resuming mid-flow

Read the clone to find where a repository stands: a
`.research/record.json` and preregistered main.tex with stub
Results/Discussion and no
`.research/results/` means `write-experiment-code` (or, with `src/`
already written, `run-experiments`) is next; results with a
provenance manifest but placeholder values means `analyze-results`
then `publish-paper`; a `values.tex` with real numbers means
`publish-paper` (its local stage if not yet green, its CI stage
otherwise). When in doubt, ask the user what has already happened
rather than re-running a step.

## Running unattended

- Long-running tools return immediately; never block waiting — poll
  between other work.
- When a step fails, go back only as far as the failure requires: a
  failed run means fixing code and re-running, not re-deriving the
  hypothesis. Re-run a step only when its *inputs* changed.
- Stop and ask the user when the research direction is genuinely
  underdetermined, or when a step has failed the same way twice —
  a third identical attempt rarely differs.
