---
name: hypothesize-and-design
description: Author a falsifiable research hypothesis and an experimental design that fixes run ids, metrics, models, datasets and the compute environment, using AIRAS's curated prompts. Use to create or rework a hypothesis and its experimental design.
---

# Hypothesize & design

Needs a `research_study_list` (prior work to build on).

1. **Author the hypothesis** via `get_generation_prompt("hypothesis",
   ...)` with the study list. Write the prose in Japanese;
   `primary_metric` / `supporting_metrics` stay English identifiers
   (parsed downstream).
2. **Fix the compute target first**: ask the user if it is not known,
   record GPU and `arch` (`x86_64`/`aarch64`) — the design and later
   the dependency lockfile depend on it.
3. **Author the design** via
   `get_generation_prompt("experimental_design", ...)`.
   `retrieve_models` / `retrieve_datasets` list curated candidates (no
   key needed); pass those rather than the prompt's built-in
   language-model defaults for any other field.
4. **Leave run ids and metrics settled.** Downstream tooling addresses
   every result as `<run_id>.<metric.path>` (e.g. `proposed.accuracy`),
   so a design that leaves run naming open is not finished. State the
   expected magnitude of the effect as an interval (a range, not a
   point) and what outcome would refute the hypothesis — a hypothesis
   without a refutation condition is not testable.

**Output**: hypothesis + experimental design, written to
`.research/research_history.json` in the experiment repository when one
exists (state belongs in the clone, not the conversation). This is the
working draft: `preregister-paper` freezes it into the canonical
`.research/record.json`, after which revision is append-only.
