# AIRAS Domain Knowledge

Curated, original engineering notes that AIRAS serves to research agents via
the `list_domain_knowledge` / `get_domain_knowledge` MCP tools. Each note is
a short, actionable quick reference (roughly 50-120 lines) tied to how AIRAS
actually runs experiments: sanity-check-first execution, GitHub Actions /
AIXS backends, and Weights & Biases tracking.

## Scope: pipeline knowledge only

This registry deliberately covers **AIRAS-pipeline-specific knowledge** —
what an agent needs to succeed inside AIRAS's contracts (sanity/main
workflows, CI runners, results files, W&B conventions).

**Library-specific engineering knowledge** (fine-tuning frameworks,
distributed training, inference servers, interpretability tooling, ...) is
intentionally *not* duplicated here. It is served by external skill
libraries — primarily [AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)
(Orchestra Research, MIT) — which the experiment template's code-generation
workflows already install on their runners
(`npx @orchestra-research/ai-research-skills`). In addition,
`resources/libraries/library_docs.py` (served by the `get_library_docs`
MCP tool) maps each common library to its official docs, GitHub, and
`llms.txt` endpoints so agents can fetch the *current* documentation at
experiment-writing time. Vendoring those notes here would mean tracking
~100 upstream skills for staleness; referencing the living upstream does
not. Do not add notes that merely restate a library's documentation — if
it isn't about the AIRAS pipeline, it belongs upstream.

## File format

One Markdown file per note, grouped in a category directory, with YAML
frontmatter:

```markdown
---
name: low-vram-fine-tuning            # unique kebab-case id
description: One-line summary used in the index and for relevance decisions.
category: resource_constrained_training   # matches the directory name
tags: [fine-tuning, vram, lora]
dependent_packages: [peft, transformers]  # optional
sources:                                  # official docs backing the note
  - https://huggingface.co/docs/peft
updated: "2026-07-19"
---

Body: the quick reference itself.
```

`name`, `description`, and `category` are required; files missing them are
skipped with a warning. Adding a new note requires no code change — the
loader discovers `*.md` files (except this README) at import time.

## Authoring rules

- **Original writing only.** Never paste text from external documentation,
  blog posts, or other skill libraries. Summarize in your own words and link
  the source in `sources:`. If a note is adapted (not just informed by)
  externally licensed material, record the origin and license in
  `THIRD_PARTY_NOTICES` at the repository root and in `sources:`.
- **Quick reference, not a manual.** State the decision rule or the pitfall
  and the fix; link official docs for the long version. No 300KB dumps.
- **Tie it to the AIRAS pipeline where possible.** Notes earn their place by
  helping an agent succeed inside AIRAS's contract (sanity/main modes, CI
  runners, W&B conventions), not by restating a library's README.
- **Version-sensitive claims must name the version** (e.g. "as of
  transformers 4.x") and set `updated:` so stale notes can be audited.
