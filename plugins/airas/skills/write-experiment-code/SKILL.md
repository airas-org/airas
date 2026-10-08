---
name: write-experiment-code
description: Produce the experiment code in an AIRAS experiment repository — against the execution contract stated here and the airas-eval input schema, with the environment fixed by lockfile and Dockerfile. Comes before the freeze — the design is settled, the record is not yet written. Use to write, fix, or regenerate experiment code, whether authored directly or via an external code-generation tool.
---

# Write the experiment code

Needs a clone with the agreed design committed as
`.research/design.json` (the `preregister_record` arguments: run ids,
params, metrics) and the execution platform settled — the platform's reference
under `_shared/references/` states the architecture and environment
constraints the code must satisfy, so read it before writing. The
record may not exist yet: `preregister-paper` freezes it on top of this
code.

However the code is produced — authored here or by an external
code-generation tool — the contract below is what the repository holds
it to; swapping the producer changes nothing else.

This contract is for experiment runs (a claim with `verifier.kind =
seyval`). A claim proved in Lean is written under `lean/` instead, to the
contract in `_shared/references/lean.md`; both kinds start through the same
`make run` and can live in one repository.

1. **Read the contract**: `get_prompts(step="experiment_code")` returns
   it; the runs it binds you to are in `.research/design.json` (in
   `.research/record.json` once frozen) and the eval plan is
   `.research/evaluation.json` — the files you may touch, the fixed CLI shape, the three modes and their
   validation lines, the three files verification reads, how the outputs
   feed airas-eval, and how the environment is pinned. Run ids and
   metric paths come from the record; a claim whose metric the code never
   emits can never be realized. Library docs via `get_library_docs`.
2. **Declare the eval plan first**: `.research/evaluation.json` with the
   task types the design calls for; `make schema` and `make list-tasks`
   read it and say what the prediction files must contain.
3. **Write the code and fix the environment**: the files the contract
   names, `pyproject.toml` pinned, `uv.lock` committed, a Dockerfile that
   builds from the lock alone for the platform reference's target. With
   an upstream implementation, write only what the design's method map
   assigns to you: the glue to the upstream entry points and the steps
   the upstream cannot carry. Never re-implement a step it provides, and
   never modify it (airas #1098).
4. **Prove it runs before handing it over**: `mode=sanity` locally until
   it prints `SANITY_VALIDATION: PASS`, then
   `make validate-inputs RUN_ID=<sanity run id>` to check the
   prediction files against the eval contract without scoring.
   Commit and push.
5. **One sanity run on the platform** (`run-experiments`, steps 2–3; a
   sanity run needs no declaration in the record). A local run proves
   nothing about the target architecture or the model the run will
   talk to. Read what the run read and called: every value it took and
   every upstream function it reached must be covered by the design's
   `params`, and a model server started outside the platform must be
   committed and referenced from the run yaml. Fix the code or the
   design and repeat until the sanity run touches nothing undeclared.
   Then put the upstream / own-code boundary in the hypothesis's
   `notes` in numbers: the upstream calls and loaded files from
   `observed.json`, the `src/` lines that implement method steps, and
   the deviations the map listed.
   Until the runtime observation lands (`observed.json`, airas #1092),
   this is a static audit: read the run yaml, `config/config.yaml`, the
   Dockerfile and the code the run executed, and compare them with
   `params` yourself — `get_experiment_run_status` returns only the log
   tail.

**Output**: committed, pushed experiment code that passes local sanity,
input validation and one platform sanity run, with `uv.lock` and a
Dockerfile that fix its environment — what `preregister-paper` freezes
on top of.
