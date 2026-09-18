write_experiment_code_prompt = """\
You are writing the experiment code of a preregistered study, into the \
clone. The repository ships empty source files; the contract below is what \
they must become. However the code is produced, this is what the \
repository holds it to.

## What you work from
`.research/record.json`: every declared run (`run_id`, `params`) and the \
metric each claim's criterion reads — these names are the contract, not \
suggestions. `.research/evaluation.json`: the eval plan (write it first if \
it still says `REPLACE_ME`). The platform reference under \
`_shared/references/` for the compute target's constraints.

## The execution contract
Run ids and output metric paths must match the record exactly — \
verification rejects results directories no declared run accounts for, \
and a claim whose metric the code never emits can never be realized. \
Library docs via `get_library_docs`.

Edit or create ONLY these files (`.github/` is managed by AIRAS, and \
everything must run on a Linux runner):

| Path | Role |
| --- | --- |
| `Dockerfile` | Reproducible environment (Python 3.11 + uv) |
| `config/config.yaml` | Shared Hydra defaults |
| `config/run/*.yaml` | One run config per declared run_id |
| `src/main.py` | Orchestrator for a single `run_id` (Hydra entrypoint) |
| `src/preprocess.py` | Dataset loading / preprocessing |
| `src/train.py` / `src/inference.py` | Single-run executor |
| `src/model.py` | Model definition, if a custom one is needed |
| `src/evaluate.py` | Independent aggregation script |
| `pyproject.toml` | Dependencies only |

The CLI shape is fixed — the Makefile's `run` target and the executors \
call exactly this, so it cannot change:

    uv run python -u -m src.main run={run_id} results_dir=.research/results mode={sanity|pilot|full}
    uv run python -u -m src.evaluate results_dir=.research/results run_ids='["run-1","run-2"]'

`run_ids` is a Hydra list override and arrives in either spelling — quoted \
JSON as above, or the quote-free `run_ids=[run-1,run-2]` the executors use \
— so parse it as Hydra does, not with `json.loads`.

All three modes must work, on the same dataset and model — only the scale \
changes: `sanity` cheap enough to run locally on CPU (1 epoch, 1–2 \
batches, or 5–10 inference samples), `pilot` 20–30% of full (≥3 epochs, \
≥50 samples) for a go/no-go, `full` the real thing. `sanity` and `pilot` \
log to `{project}-sanity` / `{project}-pilot` so they never pollute the \
full runs. `sanity` prints `SANITY_VALIDATION: PASS` with a \
`SANITY_VALIDATION_SUMMARY: {...}` line, or `SANITY_VALIDATION: FAIL \
reason=<short_reason>`; `pilot` prints the `PILOT_VALIDATION` equivalents. \
Checks, adapted to the task: ≥5 steps with final loss ≤ initial, or ≥5 \
non-identical outputs; every metric finite; `FAIL reason=missing_metrics` \
when they are absent.

## The three files verification reads
Per run, under `{results_dir}/{run_id}/`:

| File | Written by | Why it is required |
| --- | --- | --- |
| `eval_inputs/<task>.json` | `src/main.py` | the raw predictions; what the metrics can be re-derived from |
| `evaluation/<task>.json` | `make evaluate` | airas-eval's verdict, its versions and `skipped` |
| `metrics.json` | `src/evaluate.py` | copied from the airas-eval report; the file the record is checked against |

Do not write out the resolved configuration: the record takes the \
parameters a run executed with from the platform's record of the \
dispatch, never from a file the run wrote. All three go under \
`.research/results/` — the only tree the executor collects back. \
`src/evaluate.py` computes no metric of its own: it copies airas-eval's \
numbers into `metrics.json` and builds the figures.

## Feeding airas-eval
`make schema` prints the JSON Schema the prediction files must match and \
`make list-tasks` what each planned task type returns; design \
`src/evaluate.py` against that schema, not against metrics you intend to \
compute yourself.

## The environment
Pin dependencies in `pyproject.toml`, commit `uv.lock`, and provide a \
Dockerfile that builds from the lock alone, for the compute target the \
design fixed.

Produce the files as `{"files": {"<relative path>": "<content>"}}`, then \
run `mode=sanity` locally until it prints `SANITY_VALIDATION: PASS` and \
`make validate-inputs RUN_ID=<sanity run id>` before committing.
"""
