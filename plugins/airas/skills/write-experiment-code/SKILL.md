---
name: write-experiment-code
description: Produce the experiment code in an AIRAS experiment repository — against the execution contract stated here and the airas-eval input schema, with the environment fixed by lockfile and Dockerfile. Use to write, fix, or regenerate experiment code, whether authored directly or via an external code-generation tool.
---

# Write the experiment code

Needs a clone with its research context committed and the execution
platform settled — the platform's reference under `_shared/references/`
states the architecture and environment constraints the code must
satisfy, so read it before writing.

However the code is produced — authored here or by an external
code-generation tool — the contract below is what the repository holds
it to; swapping the producer changes nothing else.

This contract is for experiment runs (a claim with `verifier.kind =
seyval`). A claim proved in Lean is written under `lean/` instead, to the
contract in `_shared/references/lean.md`; both kinds start through the same
`make run` and can live in one repository.

1. **Read the contract**: `get_prompts(step="experiment_code")` returns
   it; the runs it binds you to are in `.research/record.json` and the
   eval plan in `.research/evaluation.json` — the files you may touch, the fixed CLI shape, the three modes and their
   validation lines, the three files verification reads, how the outputs
   feed airas-eval, and how the environment is pinned. Run ids and
   metric paths come from the record; a claim whose metric the code never
   emits can never be realized. Library docs via `get_library_docs`.
2. **Declare the eval plan first**: `.research/evaluation.json` with the
   task types the design calls for; `make schema` and `make list-tasks`
   read it and say what the prediction files must contain.
3. **Write the code and fix the environment**: the files the contract
   names, `pyproject.toml` pinned, `uv.lock` committed, a Dockerfile that
   builds from the lock alone for the platform reference's target.
4. **Prove it runs before handing it over**: `mode=sanity` locally until
   it prints `SANITY_VALIDATION: PASS`, then
   `make validate-inputs RUN_ID=<sanity run id>` to check the
   prediction files against the eval contract without scoring.
   Commit and push.

**Output**: committed, pushed experiment code that passes local sanity
and input validation, with `uv.lock` and a Dockerfile that fix its
environment.
