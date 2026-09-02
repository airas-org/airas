---
name: write-experiment-code
description: Produce the experiment code in an AIRAS experiment repository — against the repository's AGENTS.md contract and the airas-eval input schema, with the environment fixed by lockfile and Dockerfile. Use to write, fix, or regenerate experiment code, whether authored directly or via an external code-generation tool.
---

# Write the experiment code

Needs a clone with its research context committed and the execution
platform settled — the platform's reference under `_shared/references/`
states the architecture and environment constraints the code must
satisfy, so read it before writing.

However the code is produced — authored here or by an external
code-generation tool — the contract below is what the repository holds
it to; swapping the producer changes nothing else.

1. **The repository's `AGENTS.md` is the contract** — files you may
   touch, the exact CLI
   (`uv run python -u -m src.main run={run_id} results_dir=... mode={mode}`),
   sanity/pilot/full semantics, verdict lines, run-id naming.
   Library docs via `get_library_docs`.
2. **The outputs must feed airas-eval.** First declare the eval plan:
   write `.research/evaluation.json` with the task types the
   experimental design calls for — the template ships
   `{"task_types": ["REPLACE_ME"]}`, and `make schema`,
   `make list-tasks` and every later `make evaluate` read this file.
   The template's Makefile
   scores runs mechanically from raw predictions, so the experiment
   must write prediction files matching the eval plan's contract:
   `make schema` prints the JSON Schema the code must produce, and
   `make list-tasks` what each planned task type returns. Design
   `src/evaluate.py` output against that schema, not against metrics
   you intend to compute yourself.
3. **Fix the environment in the repository.** Pin dependencies in
   `pyproject.toml` and commit `uv.lock`; provide a Dockerfile that
   builds the environment from the lock alone. The platform reference
   has the specifics (base image, wheel availability on the target
   architecture, what a local pass does and does not prove).
4. **Prove it runs before handing it over**: run `mode=sanity` locally
   until it prints `SANITY_VALIDATION: PASS`, then
   `make validate-inputs RUN_ID=<sanity run id>` to check the
   prediction files against the eval contract without scoring.
   Commit and push.

**Output**: committed, pushed experiment code that passes local sanity
and input validation, with `uv.lock` and a Dockerfile that fix its
environment.
