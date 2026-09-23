# airas-loop policy

Operational choices for every research the loop runs. `airas loop` hands
this file to the agent at the start of each session, in place of the
questions "Settle once, up front" would otherwise ask.

- repository visibility: public (`is_private=False`)
- execution platform: seyval, BYO compute
  - workspace_id: <fill in>
  - compute_id: <fill in, resolve with list_computes each time>
- compute target: GB200 (aarch64), 1 GPU, time_limit 24h
- when a step has failed the same way twice: archive the repository and stop

## Research area: improving LLM agents on SciGym

SciGym (h4duan/SciGym, arXiv:2507.02083) hands an LLM an SBML model with
every reaction removed and lets it run simulation experiments on the true
model to recover the missing mechanism. Experiments run on RIKYU through
Seyval; the data sit next to them under `/data1/rkp00041/scigym_improvement`,
mounted read-only into every run. Its `README.md` is the full guide: read
it in the sanity run before fixing the experimental design.

- `data/scigym/` — the official repository at commit 88a7b93 (do not edit).
  `scigym.main` does not run; use `scripts/run_scigym.py` (OpenAI-compatible
  API: `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `--model_name`).
- `data/scigym_sbml/small/<BIOMD…>/` — 137 instances evaluated in the paper;
  `large/` — 213 heavier ones. Each has `truth.xml`, `partial.xml`,
  `truth.sedml`. Compare with the paper on `small`.
- Build your own environment in the experiment repository (Dockerfile +
  `uv.lock`, aarch64). `pyproject.toml` and the README's 環境構築 section
  list the pins that work there (libroadrunner 2.7.0 instead of the official
  2.8.0, antimony 2.14.0, `lib/libXrender.so.1`). One instance per process.
- Results land in `<output_dir>/<instance>/<model>/<time>/evaluation.json`
  (`observe_smape`, `rp_f1`, `rpm_f1`, …); the default config's
  `max_iterations: 5` is a smoke-test value, match the paper before comparing.
- Models: RIKYU API (`https://api.rikyu.r-ccs.riken.jp/v1`, e.g.
  `qwen3.8-27b`) or Vercel AI Gateway (`google/gemini-2.5-pro`, the paper's
  best); a self-hosted NIM is also possible.
