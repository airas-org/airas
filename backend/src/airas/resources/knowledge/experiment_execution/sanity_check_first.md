---
name: sanity-check-first
description: Design experiment code so a minutes-long sanity run exercises the full pipeline before any GPU-scale spend.
category: experiment_execution
tags: [sanity-check, validation, experiment-design, debugging]
sources:
  - https://github.com/airas-org/airas-template
updated: "2026-07-19"
---

# Sanity check first

AIRAS runs every experiment twice: `workflow="sanity_check"` (fast, cheap)
before `workflow="main"` (full scale). The single most common source of
wasted GPU time is a main run that dies on a bug a sanity run would have
caught in two minutes. Write the code so the sanity run is a faithful
miniature of the main run, not a separate code path.

## Rules

- **One code path, size controlled by config.** The mode flag must only
  shrink numbers (dataset slice, steps, model size, eval samples) — never
  branch into different logic. A `if mode == "sanity"` that skips evaluation
  means evaluation ships untested.
- **Reach the end.** A sanity run must touch every stage: data loading →
  preprocessing → training step(s) → evaluation → metric computation →
  artifact/result writing. Finishing training but crashing in plotting still
  wastes the main run.
- **Budget: minutes, CPU-sized.** Target well under 5 minutes. Use a slice
  of tens-to-hundreds of samples, 2-10 optimizer steps, and the smallest
  model variant that has the same interface (e.g. a 2-layer config of the
  same architecture rather than a different architecture).
- **Assert, don't eyeball.** End the run with explicit checks and print a
  machine-readable verdict line (the AIRAS template contract expects
  `SANITY_VALIDATION: PASS` / `FAIL`). Useful assertions:
  - loss is finite after every logged step (`math.isfinite`);
  - every metric the design promises is present in the results dict;
  - result files/artifacts exist and are non-empty at their contracted paths;
  - tensor shapes at module boundaries match the design.
- **Fail loudly and early.** `raise` on bad config instead of falling back to
  defaults; a silent fallback passes sanity and corrupts the main result.

## What sanity cannot catch — handle at design time

- **Out-of-memory at full scale.** Estimate VRAM before dispatch (see
  `low-vram-fine-tuning`) and log tensor/batch shapes so the first OOM is
  diagnosable from the stderr tail alone.
- **Slow convergence / wrong hyperparameters.** Sanity validates plumbing,
  not science. If the hypothesis is sensitive to training length, add an
  intermediate pilot scale rather than stretching the sanity budget.
- **Distribution shift from the data slice.** Slice by random sample (fixed
  seed), not `head(n)` — sorted files often make the first n samples
  degenerate (one class, one length).
