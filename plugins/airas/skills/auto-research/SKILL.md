---
name: auto-research
description: End-to-end automated research with the AIRAS integrity flow — the paper is preregistered (claims, criteria and expected results frozen in git, on top of the experiment code) before any pilot or full run, and every reported number is realized and verified from run outputs afterwards. This skill holds only the ordering and the rules that span steps; each step's contract lives in its own skill. Use when the user wants to run an AIRAS research project start to finish, or asks where in the flow they are or what comes next.
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
- `search-papers` — literature found and downloaded
- `hypothesize-and-design` — papers read, falsifiable hypothesis; run
  ids, metrics and params settled, **agreed with the user before any
  code is written** and committed as `.research/design.json` (the exact
  `preregister_record` arguments); loops back to `search-papers` as
  needed
- `write-experiment-code` — code to the execution and airas-eval
  contracts, environment fixed by lockfile + Dockerfile; local sanity,
  then **one sanity run on the platform**. What that run reads and
  calls is what the design must declare, so this step and the design
  loop until the sanity run touches nothing undeclared
- `preregister-paper` — the full paper written and committed **on top
  of the code, before any pilot or full run**; this commit is the
  freeze point. The record's `notes` say how many design ⇄ sanity
  rounds preceded it and what each changed
- `run-experiments` — pilot, then full, on the platform; bring results
  back with provenance
- `analyze-results` — analysis and verifiable figures
- `publish-paper` — numbers realized from declarations, compile +
  recompute + provenance checks until green locally, then push: CI
  re-runs the verification, builds the PDF, commits it back onto the
  protected branch as `paper.pdf` and uploads it as the artifact — the
  paper of record — which is handed to the user, state persisted

Execution platform references live in `_shared/references/` per
platform.

## Settle once, up front

Operational choices otherwise surface one tool default at a time,
mid-flow. Ask the user for them together before starting the flow and
carry the answers through the session:

- repository visibility — create it **public** (`is_private=False`)
  unless the user says otherwise: on GitHub's free plan branch
  protection, which is what makes the record gate binding, is only
  available on public repositories
- execution platform; for Seyval, managed vs **BYO** compute and, when
  several exist, which workspace
- compute target (GPU and architecture) — the experimental design and
  the dependency lockfile depend on it
- the two verifier models of `verify_paper_values`, both written into
  the record with every judgment, so keep each the same across the
  user's studies rather than falling back to whatever key happens to
  work: `citation_verifier_model` reads each passage citation (`gpt-4.1`
  unless the user names another); `implementation_verifier_model` reads
  each design's code and runs against the design
  (`vercel_ai_gateway/openai/gpt-6-luna` unless the user names another)

## Invariants across steps

These are the orchestrator's own rules; no step may relax them.

- **No pilot or full run is dispatched before the freeze commit
  exists.** Sanity runs may precede it — their outputs are never
  imported and carry no evidence — but the pilot and full phase of
  `run-experiments` must not start until `preregister-paper` has
  committed. There is no pre-freeze pilot: a predicted interval rests
  on the literature and may miss. Carry the freeze commit sha through
  the session and report it to the user; verification argues from runs
  being descendants of it.
- **Everything a run reads is in the repository or the platform's
  record.** A model server you start outside the platform (Slurm
  script, `.args`) is committed and referenced from the run yaml; a
  value the code hardcodes or reads from the environment is an
  undeclared input.
- **Runs descend from the freeze commit.** Fixes are committed on top
  of it, never instead of it — no amending or rebasing away the
  prereg commit.
- **The record only ever grows.** `.research/record.json` is a tree:
  hypotheses → claims → designs → runs → results. Every committed
  revision must *contain* the one before it whole, so a reworded claim,
  a changed run condition, a reordered list and a dropped result all
  fail the same check. Revision is an append with the **same id** (the
  later entry is the live one, the earlier stays readable); retirement
  is an append with `"withdrawn": true`. Re-running an experiment
  appends a result rather than replacing one, so "we ran it three
  times" stays in the record. A claim that fails is reported as a negative result,
  not deleted or reworded into something the data supports; new
  findings enter as new, explicitly exploratory claims declared and
  committed *before* their confirmation run — declare before you run — the record cannot yet tell the two apart.
- **No experimental number is ever typed.** Numbers reach the paper
  only as `\airasval{...}` — a run's metric, or a condition the run
  was declared with — and through declared
  tables and charts; anything else is `\unverified{...}` and said to
  the user. This covers the experimental setup too, not just results:
  a stated batch size the run never used is the same defect as a
  fabricated accuracy.
- **State handoff is the repository.** Everything a later step needs
  must be committed, not held in conversation — a fresh session must
  be able to resume from the clone alone.
- **Every turn ends in a fork point.** The harness's hooks, not the
  agent, record the trace: entering a step skill is logged, and at the
  end of every turn this session and harness are captured into
  `.research/sessions/` and the whole tree is committed. That commit
  is a fork point anyone can resume from with `airas session import`
  — same agent, another model or harness, or another method. Push so
  it is shared; never amend or rebase those commits away.

## The integrity model — why the gate holds

Two rules generate every check; reason from them when a situation the
steps don't cover comes up.

1. The agent authors only *declarations* (append-only, revision = a
   later entry with the same id) and prose. Every number, result and
   verified flag in record.json is machine-derived.
2. Anything machine-derived must equal its re-derivation at
   verification time. Nothing is trusted for *who* wrote or committed
   it — content is judged, authorship is not.

`verified` is therefore never set by hand, only derived: every run
under the claim has results. It goes from false to true once and never
back; a stored true the results no longer bear out fails verification.

**`verified` says the data is in, not that the claim held.** Whether
the claim held is `verdict`, derived from the criterion the claim
declared (supported / refuted; inconclusive when the metric cannot be
resolved) and likewise written once. Whether the claim was declared
before its runs executed is not modelled yet (TODO) — that order
discipline is the agent's. A refuted claim is a negative result,
reported as such; reading a column of `verified: true` as "the
hypothesis held" is the misreading to avoid.

Trust domains: local runs of the checks have **zero evidentiary
value** — the local toolchain is in the agent's hands, and whatever a
local check reports the agent can push anyway, so it is advice and not
a gate. `update_record` therefore writes and commits without judging.
The judgement is the CI run on the pushed history, anchored by two
stores the agent cannot write: Seyval's run records (execution id,
commit hash, output bytes) and git's content-addressed history. What
makes that judgement binding rather than informative is branch
protection, set up by `prepare_repository`: the record gate is a
required check on the protected branch, enforced on admins too, so a
commit whose check is red cannot land at all. Work is pushed to a
staging ref for the gate to run on, then fast-forwarded onto the
protected branch, which lands the exact sha CI judged.

Consequences: rewriting a committed declaration turns the branch
permanently red (the history walk sees every version); forged numbers,
metrics or flags fail recomputation or the Seyval byte-comparison;
rewriting history after a run detaches the run's commit from HEAD and
voids the results themselves — which is why force pushes, deletions
and squash/rebase merges are all disabled rather than merely
discouraged. Before any run exists, redoing the record is legitimate —
nothing is anchored yet, so nothing can be hidden.

## Resuming mid-flow

`.research/trace/steps.jsonl` says which step was entered last and how
many times each has run; `.research/derived_from.json` says this clone was
forked from another repository's fork point. Otherwise read the clone
to find where it stands: a
`.research/design.json` and no `src/` means `write-experiment-code`
is next; `src/` written but no `.research/record.json` means
`preregister-paper` is next (after the platform sanity run);
`.research/record.json` and preregistered main.tex with stub
Results/Discussion and no `.research/results/` means
`run-experiments` is next; results with a
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

When nobody is watching — the session was started by `airas loop`,
which hands you a policy in its prompt — three things change, and
nothing else:

- **The policy answers "Settle once, up front".** Read visibility,
  execution platform and compute target from the policy in the prompt
  instead of asking. It lives in the airas repository
  (`.github/airas-loop-policy.md`), once for every research the loop runs.
- **Waiting is allowed.** Estimate how long a run will take and `sleep`
  for that long in one command before checking again; the loop raises
  the shell timeout so a single sleep can span hours. Polling every few
  minutes wastes turns. If the same wait comes round three times with
  nothing having moved, the run is stuck: treat it as a failure and
  archive, as below.
- **Asking becomes archiving.** Where this file says "ask the user",
  commit a note with what needs deciding, archive the repository
  (`gh repo archive`) and end the turn. A human unarchives it to resume;
  the loop starts the next research meanwhile.

Ending the turn is how a research ends: once the paper of record is on
the protected branch there is nothing more to do, and the loop starts
the next one.
