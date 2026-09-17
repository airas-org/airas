---
name: hypothesize-and-design
description: Read the downloaded papers, then author a falsifiable research hypothesis and an experimental design that fixes run ids, metrics, models, datasets and the compute environment. Use to create or rework a hypothesis and its experimental design.
---

# Hypothesize & design

Starts from the search rows and `fulltext_path`s `search-papers` left.
This is a loop, not a pass: read, hypothesize, notice what the
literature does not settle, go back to `search-papers` for it, and
refine until the hypothesis rests on passages you have actually read.

1. **Read** the downloaded papers with your own tools — a paper runs to
   80k+ characters, so read in parts or search within the file. Keep,
   per paper the research will rest on, its identifiers, its
   `fulltext_path` and the passages that matter (page and verbatim
   quote): `preregister_record` takes exactly these, and assigns ids in
   the order given (`s1`, `s2`, …; `p1`, `p2`, … within a source), so
   note which passages the hypothesis answers (its gap) and which the
   design follows for `grounded_on` and `cites_passages`. A quote is
   matched against the snapshot ignoring line breaks, end-of-line
   hyphenation and ligatures, so copy it as the extracted text has it;
   keep it to one passage on one page (pages are separated by form
   feeds and a quote cannot span two).
2. **Author the hypothesis** yourself: one statement, the gap in the
   read papers it answers, and what would refute it. Write the prose in
   Japanese; metric names stay English identifiers (parsed downstream).
   A gap the papers at hand cannot confirm is a reason to search again,
   not to assume.
3. **Fix the compute target first**: ask the user if it is not known,
   record GPU and `arch` (`x86_64`/`aarch64`) — the design and later
   the dependency lockfile depend on it.
4. **Author the design** yourself: the runs to compare (proposed,
   baselines, ablations), the models and datasets, the metrics, and the
   compute they need. `retrieve_models` / `retrieve_datasets` list
   curated candidates (no key needed); prefer those to defaults from
   memory, and `search_huggingface_hub` when the curated lists lack
   what the design needs.
5. **Leave run ids and metrics settled.** Downstream tooling addresses
   every result as `<run_id>.<metric.path>` (e.g. `proposed.accuracy`),
   so a design that leaves run naming open is not finished. State the
   expected magnitude of the effect as an interval (a range, not a
   point) and what outcome would refute the hypothesis — a hypothesis
   without a refutation condition is not testable. These become each
   claim's `prediction` and `criterion` (a threshold on one named
   metric, one run against another or a constant) at preregistration.
   For each claim, say why its holding is evidence for the hypothesis
   (its `rationale`), and list what the claims together still assume
   in order to imply the hypothesis (the hypothesis's `assumptions`).

**Output**: hypothesis + experimental design, and the papers they rest
on with their `fulltext_path` and quoted passages. Nothing is in the
record yet: `preregister-paper` freezes all of it into the canonical
`.research/record.json`, after which revision is append-only. What the
declarations cannot carry — the gap in prose, why each margin and
interval was chosen, the compute target, the run-to-claim table — goes
into the hypothesis's `notes` in that same call, so it is frozen with the
record and a fresh session reads it from the clone; do not keep a draft
file beside the record.
