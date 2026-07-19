---
name: wandb-for-automated-experiments
description: Weights & Biases conventions for agent-run experiments — grouping, config logging, summary metrics, and offline fallback.
category: experiment_tracking
tags: [wandb, experiment-tracking, logging, metrics]
dependent_packages: [wandb]
sources:
  - https://docs.wandb.ai/guides/track
updated: "2026-07-19"
---

# W&B for automated experiments

AIRAS passes a `wandb_config` into the experiment repo, and downstream steps
(`fetch_experiment_results`, `analyze_experiment`, the paper) consume what
the runs logged. Log for those consumers, not for a human watching a
dashboard live.

## Run identity

- **One `wandb.init` per experimental condition**, with a name that encodes
  what varies: `"{method}-seed{seed}"` beats an auto-generated name when the
  analysis step has to match runs to design conditions.
- **`group`** ties the repeats of one condition together (e.g.
  `group="proposed-lr3e-4"`), so seed-averaged views come for free.
- **Tag the pipeline stage**: `tags=["sanity_check"]` vs `tags=["main"]`.
  Sanity runs must never be aggregated into reported results.

## What to log

- **The full resolved config** at init (`config=vars(args)` or the config
  dict), including the seed and dataset slice sizes. If it isn't in the
  config, the run can't be reproduced or compared.
- **Curves at a sane cadence**: per-epoch or every N steps. Per-step logging
  of dozens of scalars slows small experiments and buries the signal.
- **Final headline metrics into `run.summary`** explicitly (or via
  `define_metric(..., summary="max")`). Downstream analysis reads summaries;
  a metric that only exists as a curve forces fragile last-point extraction.
- **`wandb.finish()` at the end** (and let exceptions propagate so the run
  is marked failed, not silently truncated).

## Robustness in CI

- The run must not die because tracking died. If no API key is present,
  fall back instead of crashing:
  `os.environ.setdefault("WANDB_MODE", "offline")` — the experiment still
  writes its local results files, which remain the source of truth.
- **W&B is a mirror, not the results store.** The contracted results files
  in the repo/artifacts are what AIRAS collects; every number needed by the
  paper must exist there even if the W&B upload never happened.
