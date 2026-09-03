---
name: run-experiments
description: Execute committed experiment code on the chosen compute platform (GitHub Actions or Seyval) and bring the outputs back into the repository with provenance. Use to run, monitor, or re-run experiments in an AIRAS experiment repository.
---

# Run the experiments

Needs a clone with committed experiment code that passes local sanity
(built to the `write-experiment-code` contract, `uv.lock` committed). Every run you
dispatch must already be declared in `.research/record.json` **in a
commit the run will execute** — results for an undeclared run_id fail
verification, and a claim is verified once every run under it has results — but declare before you dispatch: the record cannot yet tell a preregistered claim from a post-hoc one. Declare late additions with `append_to_record`
(it commits the append itself) and push before dispatching.

1. **Resolve the platform.** It should already be settled — the code
   was written against its architecture and environment constraints.
   Read its reference in full; it is the procedure for steps 2-3.
   This file states only what every platform must deliver, so a
   platform is added by adding a reference that answers the same three
   questions — how the contract CLI is launched, how the run's
   identifier and commit are obtained, and how its outputs reach the
   repository.

   | Platform | Reference |
   |---|---|
   | GitHub Actions | `_shared/references/github-actions.md` |
   | Seyval | `_shared/references/seyval.md` |

2. **Run it** by the reference's procedure, then fix, commit on top and
   re-run as needed. However the run starts, record two things when it
   ends: the platform's **run identifier** and the **commit hash it
   executed**. Step 3 cannot be done without them.

3. **Make the run produce what verification reads.** The contract CLI
   (`src.main`) writes only `eval_inputs/` — the raw predictions. The
   numbers the record is checked against live in `metrics.json`, which
   the evaluation step writes, and provenance byte-compares *that* file
   against the platform's stored copy. A run that stops after `src.main`
   therefore succeeds and still fails verification, with nothing in the
   error pointing at the cause.

   So a run must carry the chain through to the end:

   ```
   src.main  &&  make evaluate RUN_ID=<run_id>  &&  src.evaluate
   ```

   On a platform that gives each run a fresh working directory, a later
   run cannot see an earlier one's output, so either chain the three in
   one dispatch or stage the earlier runs into it (Seyval:
   `inputs_from_runs`). Keep `eval_inputs/` in the results too: it is
   what the metrics can be re-derived from, and the record anchors it by
   hash.

4. **Bring the results back** under `.research/results/`, committed,
   with `.research/results/.provenance.json` declaring per results
   directory the `execution_id` and `commit_hash` from step 2.
   `verify_paper_values` pins its provenance cross-check to that file and
   treats a missing declaration as a mismatch, so results that arrive any
   other way fail verification. If the same experiment ran more than
   once, declare the run that should be reported and tell the user the
   others exist (the selection is reviewable at verification).

**Output**: committed results under `.research/results/` — `eval_inputs/`,
`metrics.json` and the evaluation report — with their provenance manifest.
