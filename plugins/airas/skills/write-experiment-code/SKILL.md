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

1. **The execution contract.** The experiment repository ships empty
   source files; this is what they must become. Run ids and output metric
   paths must match `.research/record.json` exactly — verification rejects
   results directories no declared run accounts for, and a claim whose
   metric the code never emits can never be realized. Library docs via
   `get_library_docs`.

   **Edit or create ONLY these files** (`.github/` is managed by AIRAS,
   and everything must run on a Linux runner):

   | Path | Role |
   | --- | --- |
   | `Dockerfile` | Reproducible environment (Python 3.11 + uv) |
   | `config/config.yaml` | Shared Hydra defaults |
   | `config/run/*.yaml` | One run config per (method, model, dataset) |
   | `src/main.py` | Orchestrator for a single `run_id` (Hydra entrypoint) |
   | `src/preprocess.py` | Dataset loading / preprocessing |
   | `src/train.py` / `src/inference.py` | Single-run executor |
   | `src/model.py` | Model definition, if a custom one is needed |
   | `src/evaluate.py` | Independent aggregation script |
   | `pyproject.toml` | Dependencies only |

   **The CLI shape is fixed** — `run_experiment.yml` and the external
   executors call exactly this, so it cannot change:

   ```bash
   uv run python -u -m src.main run={run_id} results_dir=.research/results mode={sanity|pilot|full}
   uv run python -u -m src.evaluate results_dir=.research/results run_ids='["run-1","run-2"]'
   ```

   **Run ids** are `{method_type}-{model}-{dataset}`, dropping whichever of
   model/dataset does not apply; `method_type` is `proposed` or
   `comparative-{index}`.

   **All three modes must work**, on the same dataset and model — only the
   scale changes: `sanity` cheap enough to run locally on CPU (1 epoch, 1–2
   batches, or 5–10 inference samples), `pilot` 20–30% of full (≥3 epochs,
   ≥50 samples) for a go/no-go, `full` the real thing. `sanity` and `pilot`
   log to `{project}-sanity` / `{project}-pilot` so they never pollute the
   full runs.

   `sanity` prints `SANITY_VALIDATION: PASS` with a
   `SANITY_VALIDATION_SUMMARY: {...}` line, or
   `SANITY_VALIDATION: FAIL reason=<short_reason>`; `pilot` prints the
   `PILOT_VALIDATION` equivalents. Checks, adapted to the task: ≥5 steps
   with final loss ≤ initial, or ≥5 non-identical outputs; every metric
   finite; `FAIL reason=missing_metrics` when they are absent. This is your
   own gate before dispatching anything expensive — nothing downstream
   parses it for you.

2. **Write the four files verification reads.** Per run, under
   `{results_dir}/{run_id}/`:

   | File | Written by | Why it is required |
   | --- | --- | --- |
   | `eval_inputs/<task>.json` | `src/main.py` | the raw predictions; what the metrics can be re-derived from |
   | `config.json` | `src/main.py` | `OmegaConf.to_container(cfg, resolve=True)` — the conditions the run actually executed under |
   | `evaluation/<task>.json` | `make evaluate` | airas-eval's verdict, its versions and `skipped` |
   | `metrics.json` | `src/evaluate.py` | copied from the airas-eval report; the file the record is checked against |

   All four go **under `.research/results/`**: that is the only tree the
   executor collects back, so anything written beside the Hydra logs or in a
   scratch directory never reaches the repository, and the check that would
   have used it silently passes on an empty value.

   `src/evaluate.py` computes no metric of its own — it copies airas-eval's
   numbers into `metrics.json` and builds the figures. Routing them through
   W&B instead would put values the experiment code wrote into the file
   verification reads, which is what the fixed evaluation layer exists to
   prevent.

3. **The outputs must feed airas-eval.** First declare the eval plan:
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
4. **Fix the environment in the repository.** Pin dependencies in
   `pyproject.toml` and commit `uv.lock`; provide a Dockerfile that
   builds the environment from the lock alone. The platform reference
   has the specifics (base image, wheel availability on the target
   architecture, what a local pass does and does not prove).
5. **Prove it runs before handing it over**: run `mode=sanity` locally
   until it prints `SANITY_VALIDATION: PASS`, then
   `make validate-inputs RUN_ID=<sanity run id>` to check the
   prediction files against the eval contract without scoring.
   Commit and push.

**Output**: committed, pushed experiment code that passes local sanity
and input validation, with `uv.lock` and a Dockerfile that fix its
environment.
