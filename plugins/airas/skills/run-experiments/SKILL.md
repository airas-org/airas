---
name: run-experiments
description: Execute committed experiment code on the chosen compute platform (GitHub Actions or Seyval) and bring the outputs back into the repository with provenance. Use to run, monitor, or re-run experiments in an AIRAS experiment repository.
---

# Run the experiments

Needs a clone with committed experiment code that passes local sanity
(built to the `AGENTS.md` contract, `uv.lock` committed).

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

3. **Bring the results back** under `.research/results/`, committed,
   with `.research/results/.provenance.json` declaring per results
   directory the `execution_id` and `commit_hash` from step 2.
   `verify_paper_values` pins its provenance cross-check to that file and
   treats a missing declaration as a mismatch, so results that arrive any
   other way fail verification. If the same experiment ran more than
   once, declare the run that should be reported and tell the user the
   others exist (the selection is reviewable at verification).

**Output**: committed results under `.research/results/` with their
provenance manifest.
