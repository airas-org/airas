---
name: github-actions-ml-experiments
description: Constraints and conventions for running ML experiment code on GitHub Actions runners (no GPU, 6-hour job limit, artifact-based results).
category: experiment_execution
tags: [github-actions, ci, runners, artifacts]
sources:
  - https://docs.github.com/en/actions/reference/limits
  - https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners
updated: "2026-07-19"
---

# ML experiments on GitHub Actions

AIRAS's default execution backend (`backend="github_actions"`) runs the
experiment inside a workflow on a GitHub-hosted runner. Design the code for
that box, or pick a GPU backend (`"aixs"`) at dispatch time.

## Runner reality

- **No GPU** on standard GitHub-hosted runners. Anything CUDA-dependent must
  either run in CPU mode (`torch.device("cpu")` fallback, small models) or be
  dispatched to a GPU backend instead. Never hard-code `.cuda()`; resolve the
  device once at startup from availability.
- **Modest resources**: standard Linux runners have 2-4 vCPUs and 7-16 GB
  RAM. A dataset that "fits in memory" on a dev machine may not here —
  stream or subsample.
- **Hard time limit: 6 hours per job** (the workflow is killed, not warned).
  Budget the main run well inside it, print progress with timestamps so a
  timeout is diagnosable, and write partial results incrementally rather
  than only at the end.
- **Ephemeral disk.** Everything not uploaded as an artifact or pushed to
  the repo is gone when the job ends.

## Conventions that make CI runs debuggable

- **stdout/stderr is the primary debugging channel.** AIRAS surfaces the
  stderr tail after failures; put the information there. Log the resolved
  config, dataset sizes, and device at startup; print one progress line per
  epoch/eval, not per step.
- **Exit codes matter.** Let exceptions propagate (non-zero exit) instead of
  catching-and-continuing; a green job with wrong results is far worse than
  a red job.
- **Results go to contracted paths.** Write metrics/figures where the
  template's workflow collects them (see the experiment repo's AGENTS.md);
  files written elsewhere silently vanish with the runner.
- **Pin the environment.** Pin dependency versions in the repo (the template
  installs from it) so a re-run months later reproduces the same stack; an
  unpinned `pip install` is a different experiment every week.
- **Cache-friendly downloads.** Large model/dataset downloads repeat on
  every run unless cached by the workflow; prefer small models and
  Hugging Face datasets with explicit `split` slicing to cut cold-start
  time.

## Choosing the backend

| Situation | Backend |
|---|---|
| Sanity check, CPU-scale pilot, analysis-only | `github_actions` |
| Training or inference that needs a GPU / >6h | `aixs` (or another GPU backend) |

Decide at design time, not after the first failed run: if the experimental
design's compute environment specifies a GPU, the main run does not belong
on a hosted runner.
