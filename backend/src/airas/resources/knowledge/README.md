# AIRAS Domain Knowledge

Curated, original engineering notes that AIRAS serves to research agents via
the `list_domain_knowledge` / `get_domain_knowledge` MCP tools. Each note is
a short, actionable quick reference (roughly 50-120 lines) tied to how AIRAS
actually runs experiments: sanity-check-first execution, GitHub Actions /
AIXS backends, and Weights & Biases tracking.

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
