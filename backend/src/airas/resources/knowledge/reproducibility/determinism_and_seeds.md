---
name: determinism-and-seeds
description: Make automated experiments reproducible — correct seeding, PyTorch determinism flags and their cost, and multi-seed reporting.
category: reproducibility
tags: [reproducibility, seeds, determinism, pytorch, statistics]
dependent_packages: [torch, numpy]
sources:
  - https://pytorch.org/docs/stable/notes/randomness.html
updated: "2026-07-19"
---

# Determinism and seeds

An automated pipeline re-runs experiments without a human noticing that two
"identical" runs differ. Reproducibility is therefore not optional polish —
it is what makes `analyze_experiment` conclusions trustworthy.

## Seeding checklist

Seed every generator that exists in the process, once, at startup:

```python
import os, random
import numpy as np
import torch

def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)          # seeds all devices, CPU and CUDA
    os.environ["PYTHONHASHSEED"] = str(seed)
```

- **DataLoader workers reseed themselves.** With `num_workers > 0`, pass a
  `worker_init_fn` (or a seeded `torch.Generator`) or per-worker numpy state
  diverges between runs.
- **Take the seed from config and log it** (config dict, W&B, stdout). A
  reproducible run with an unrecorded seed is not reproducible.
- **Shuffle/split with an explicit seeded generator**, not global state, so
  the data split is stable even if library code consumes global RNG calls.

## Bitwise determinism (when you need identical numbers)

```python
torch.use_deterministic_algorithms(True)
torch.backends.cudnn.benchmark = False
# CUDA >= 10.2 requires this for deterministic cuBLAS matmul:
os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
```

Costs and caveats:

- Deterministic kernels can be noticeably slower, and a few ops have no
  deterministic implementation — `use_deterministic_algorithms(True)` raises
  on them, which is the desired loud failure.
- Determinism holds only for the same hardware, CUDA, and library versions.
  Across a laptop and a CI runner, expect equal *conclusions*, not equal
  bits — which is one more reason to pin dependency versions.
- For most experiments, seed everything but skip the deterministic-kernel
  flags; spend the saved time on more seeds instead (below).

## One seed is an anecdote

- Run the main experiment with **at least 3 seeds** (5+ if the effect is
  small) and report mean ± standard deviation for every headline metric; a
  method comparison from single runs is noise.
- Vary **only** the seed between repeats — same data split policy, same
  hyperparameters — and keep per-seed results in the output so the analysis
  step can compute dispersion itself.
- If the compute budget forces a single seed (e.g. a large fine-tune), state
  that explicitly in the results and the paper's limitations; do not present
  a single run's decimals as stable.
