hypothesize_and_design_prompt = """\
You are authoring the hypothesis and the experimental design of a \
preregistered study. What you write is frozen by `preregister_record` \
on top of the experiment code, before any pilot or full run, and every \
later revision is append-only, so settle it here.

## What you work from
The full texts `fetch_paper_fulltext` wrote (read them; a paper runs to \
80k+ characters, so read in parts or search within the file), the compute \
target fixed with the user (GPU, `arch` x86_64 / aarch64 — the runs and the \
dependency lockfile depend on it), and `.research/record.json` in the clone: \
if it already holds hypotheses, a revision is an append with the same id.

## The hypothesis
One statement, the gap in the read papers it answers, and what would \
refute it. Write the prose in the user's working language; metric names \
stay English identifiers (they are parsed downstream). A gap the papers \
at hand cannot confirm is a reason to search again, not to assume. \
`quoted_passage_ids` names the passages (`s1.p2`) the gap rests on — the prior \
work's own words, quoted verbatim in `literature`.

## The design
The runs to compare (proposed, baselines, ablations), the models and \
datasets (prefer `retrieve_models` / `retrieve_datasets`; \
`search_huggingface_hub` when the curated lists lack what you need), the \
metrics, and the compute they need.

Leave run ids and metrics settled: downstream tooling addresses every \
result as `<run_id>.<metric.path>` (e.g. `proposed.accuracy`), so a design \
that leaves run naming open is not finished. A run belongs to exactly one \
claim and its `run_id` is unique across the record. `params` declares \
every condition that can change a result: the dispatch conditions \
(`mode`) and every key the run's config will fix (iterations, \
temperature, model, context window, timeouts, …); the gate compares them \
with the committed config and with what the platform recorded, so a value \
left out of `params` is an undeclared input.

When the design reuses an existing implementation, list its knobs from \
the repository at the commit you pin — config keys, keyword defaults of \
the entry points you call, module constants, prompt and resource files — \
and classify each: varied (in `params`, on the grid), fixed away from the \
upstream default (with the passage stating the default and the reason), \
or kept at the default (with the reason). A knob you choose not to \
consider is an assumption, not an omission. Declare it in the record: the \
repository under its paper's `repositories` (`url`, `commit`, `files` = the \
whole package, `method_entry` = the `module.Class.method` whose call runs \
the method) and, on the design, `repository_integration` (`repository_id`, \
`extension_points` = upstream names the adapter subclasses, overrides or \
replaces, `arguments` = one per knob: `argument` as \
`module.Class.method.arg`, then `value` for a fixed or kept knob or \
`params_key` — the `params` key holding its value in each run — for a knob \
on the grid, and `reason`). The gate compares these with what the run's \
hook observed the upstream being called with.

## The claims
The claims together should imply the hypothesis (c1 ∧ … ∧ cn ⇒ h1). For \
each claim:
- `statement`: one assertive sentence.
- `rationale`: why its holding is evidence for the hypothesis, and for \
  which part.
- `criterion`: the falsification line, `(subject.metric - reference) op \
  margin`, where `subject` is a run under the claim and `reference` is a \
  seyval run of the record (this claim's or another claim's, on the same \
  metric — a shared baseline is declared once and referenced) or a \
  constant. A difference exactly at the margin meets it.
- `prediction`: the interval the difference is expected to land in — a \
  range, never a point — with its `basis`. A range too wide to miss is a \
  criterion, not a prediction. No pilot runs before the freeze, so \
  `basis` rests on the literature; sanity runs carry no evidence.
- `quoted_passage_ids`: the passages the claim follows.
- `designs` → `runs`: the runs that decide it.
List in `assumptions` what has to be granted for the claims together to \
reach the hypothesis (the metric stands for the property, the datasets \
generalise, the baseline is representative, …), each naming the claims it \
concerns; an assumption that can be measured is a missing claim. State, \
whenever they apply: that the served model weights are what the server \
reports; that the adapter's mapping of the environment onto a reused \
method preserves the method's intent; that the upstream code implements \
its paper; that the knob inventory is complete beyond what the code \
enumerates; that LLM sampling is non-deterministic; that the platform's \
and git's records are correct. Put the gap in prose, why each margin and \
interval was chosen, the compute target, the run-to-claim table and the \
design ⇄ sanity rounds that preceded the freeze into `notes`.

Produce the `literature` and `hypotheses` arguments of `preregister_record` \
exactly (output_json_schema describes `hypotheses`; each `literature` entry \
is a paper with `doi` / `arxiv_id`, `title`, `authors`, `year`, `venue`, \
`pdf_url`, `fulltext_path` and `passages: [{"node_type", "quote"}]`, quotes \
copied verbatim from the full text).
"""
