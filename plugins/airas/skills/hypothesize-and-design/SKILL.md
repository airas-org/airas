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
   design follows; record both as `quoted_passage_ids`. A quote is
   matched against the snapshot ignoring line breaks, end-of-line
   hyphenation and ligatures, so copy it as the extracted text has it;
   keep it to one passage on one page (pages are separated by form
   feeds and a quote cannot span two).
2. **Fix the compute target**: ask the user if it is not known, and
   record GPU and `arch` (`x86_64`/`aarch64`) — the design and later
   the dependency lockfile depend on it.
3. **Enumerate the knobs** when the design reuses an existing
   implementation: from its repository at the commit you will pin, list
   the keys of its config files, the keyword defaults of the entry
   points you will call, its module constants, and the prompt or
   resource files it reads (by reading the code until the inventory
   tool lands). Classify each as varied (in `params`, on the grid),
   fixed away from the upstream default (with the passage stating the
   default and the reason), or kept at the default (with the reason);
   a knob you decide not to consider is an assumption, not an omission.
   Declare all of it in the record: the repository goes under its
   paper's `repositories` (`url`, `commit`, `files` naming the whole
   package, `method_entry` = the `module.Class.method` whose call runs
   the method), and the design carries `repository_integration`
   (`repository_id`, `extension_points` = upstream names your adapter
   subclasses, overrides or replaces, `arguments` = one entry per knob
   you set or keep: `argument` as `module.Class.method.arg`, `value`,
   `reason`). The run hook records what the upstream was called with,
   and the gate compares it with these.
4. **Author the hypothesis and the design** against the guide
   `get_prompts(step="hypothesis_and_design")` returns: it states what a hypothesis, a claim (statement, rationale,
   criterion, predicted interval, cited passages), a design and a run
   must contain, and ends in the exact `literature` and `hypotheses`
   arguments `preregister_record` takes. `retrieve_models` /
   `retrieve_datasets` list curated candidates; `search_huggingface_hub`
   when they lack what the design needs. A gap the papers at hand cannot
   confirm is a reason to go back to `search-papers`, not to assume.
   Write the prose in the user's working language; metric names stay
   English identifiers.
5. **Agree the design with the user before any code is written**: run
   ids, params, claims with criteria and predictions, tables. A
   consultation is not a go-ahead to build. Then write the agreed
   design to `.research/design.json` — exactly the `literature` and
   `hypotheses` arguments `preregister_record` will take — and commit
   it.

**Output**: hypothesis + experimental design, and the papers they rest
on with their `fulltext_path` and quoted passages, committed as
`.research/design.json`. Nothing is in the record yet:
`write-experiment-code` reads the draft next, and its platform sanity
run shows what the design missed (a value read, a function called, a
server started outside the platform) — fold that back into
`design.json`, then `preregister-paper` passes it to
`preregister_record`, which freezes it into the canonical
`.research/record.json` and removes the draft in the same commit, after
which revision is append-only. What the declarations cannot carry — the
gap in prose, why each margin and interval was chosen, the compute
target, the run-to-claim table — goes into the hypothesis's `notes`, so
it is frozen with the record and a fresh session reads it from the
clone.
