---
name: low-vram-fine-tuning
description: Estimate VRAM before dispatch and fit fine-tuning into a fixed GPU budget — precision, LoRA, gradient accumulation/checkpointing, in that order.
category: resource_constrained_training
tags: [fine-tuning, vram, lora, quantization, oom]
dependent_packages: [torch, transformers, peft]
sources:
  - https://huggingface.co/docs/peft
  - https://huggingface.co/docs/transformers/perf_train_gpu_one
updated: "2026-07-19"
---

# Fitting fine-tuning into a VRAM budget

The experimental design fixes the GPU (type, count, VRAM) before any code
runs, and an OOM only surfaces in the main run — the sanity check is too
small to hit it. Estimate first, then choose techniques in order of how
little they change the science.

## Back-of-envelope VRAM estimate

For full fine-tuning with Adam in mixed precision, per model parameter:

- weights (fp16/bf16): 2 bytes
- gradients: 2 bytes
- optimizer states (fp32 master weights + 2 moments): ~12 bytes

≈ **16 bytes/param** before activations — a 7B model needs ~112 GB just for
states, so full fine-tuning of 7B does **not** fit a single 80 GB GPU
without offloading. Activations come on top and scale with
`batch_size x seq_len` (and roughly quadratically with `seq_len` for
attention without kernel fusion). Rule of thumb: if params x 16 bytes is
already more than ~60% of VRAM, plan for LoRA from the start.

## Escalation ladder (change the science as little as possible)

1. **bf16/fp16 mixed precision** — near-free; prefer bf16 where supported
   (no loss-scale tuning).
2. **LoRA / QLoRA (PEFT)** — freezes base weights: gradient + optimizer
   memory shrinks to the adapter's few million params. QLoRA additionally
   holds the frozen base in 4-bit. This changes what is trained, so state
   "LoRA fine-tuning" in the design and paper, not "fine-tuning".
3. **Gradient accumulation** — keep the *effective* batch size of the
   design with a smaller per-device batch:
   `effective = per_device x accumulation_steps`. Log the effective size;
   comparisons across methods must hold it constant.
4. **Gradient checkpointing** — trades ~20-30% extra compute for large
   activation savings; combine with (3) when long sequences OOM.
5. **Shrink the model, not the question** — if 1-4 still don't fit, use a
   smaller variant of the same family at the same recipe rather than
   silently truncating sequence length or dataset, which changes the
   hypothesis being tested.

## Pitfalls

- **Effective batch size drift**: changing per-device batch without fixing
  accumulation steps quietly changes optimization dynamics between the
  baseline and the proposed method.
- **OOM in evaluation, not training**: generation with long outputs (KV
  cache) can OOM after training succeeded; cap `max_new_tokens` and eval
  batch size explicitly.
- **Fragmentation masquerading as OOM**: a failure late in training with
  "reserved but unallocated" memory in the message is fragmentation;
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` often resolves it.
- **Adapter-only artifacts**: with LoRA, save/upload the adapter (small)
  and record the exact base model id; do not ship multi-GB merged weights
  as CI artifacts.
