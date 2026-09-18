hypothesize_and_design_prompt = """\
You are authoring the hypothesis and the experimental design of a \
preregistered study. What you write is frozen by `preregister_record` \
before any experiment runs, and every later revision is append-only, so \
settle it here.

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
`grounded_on` names the passages (`s1.p2`) the gap rests on — the prior \
work's own words, quoted verbatim in `literature`.

## The design
The runs to compare (proposed, baselines, ablations), the models and \
datasets (prefer `retrieve_models` / `retrieve_datasets`; \
`search_huggingface_hub` when the curated lists lack what you need), the \
metrics, and the compute they need.

Leave run ids and metrics settled: downstream tooling addresses every \
result as `<run_id>.<metric.path>` (e.g. `proposed.accuracy`), so a design \
that leaves run naming open is not finished. A run belongs to exactly one \
claim and its `run_id` is unique across the record. `params` declares only \
what the commit cannot fix (the dispatch conditions, e.g. `{"mode": \
"full"}`); batch size, seeds and datasets live in the repository's config.

## The claims
The claims together should imply the hypothesis (c1 ∧ … ∧ cn ⇒ h1). For \
each claim:
- `statement`: one assertive sentence.
- `rationale`: why its holding is evidence for the hypothesis, and for \
  which part.
- `criterion`: the falsification line, `(subject.metric - reference) op \
  margin`, where `reference` is another run under the claim or a constant. \
  A difference exactly at the margin meets it.
- `prediction`: the interval the difference is expected to land in — a \
  range, never a point — with its `basis`. A range too wide to miss is a \
  criterion, not a prediction.
- `cites_passages`: the passages the claim follows.
- `designs` → `runs`: the runs that decide it.
List in `assumptions` what has to be granted for the claims together to \
reach the hypothesis (the metric stands for the property, the datasets \
generalise, the baseline is representative, …), each naming the claims it \
concerns; an assumption that can be measured is a missing claim. Put the \
gap in prose, why each margin and interval was chosen, the compute target \
and the run-to-claim table into `notes`.

Produce the `literature` and `hypotheses` arguments of `preregister_record` \
exactly (output_json_schema describes `hypotheses`; each `literature` entry \
is a paper with `doi` / `arxiv_id`, `title`, `authors`, `year`, `venue`, \
`pdf_url`, `fulltext_path` and `passages: [{"node_type", "quote"}]`, quotes \
copied verbatim from the full text).
"""
