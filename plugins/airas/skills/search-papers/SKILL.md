---
name: search-papers
description: Search for literature or fetch specific papers by arXiv ID or DOI through the repository's CI into .research/sources/. Use to bring literature on a topic to hand; reading and distilling it happens in hypothesize-and-design, which returns here whenever it needs more.
---

# Search papers

When the user specifies papers, call `dispatch_literature_fetch` with
`arxiv_ids` and/or `dois` instead of `query`, for example
`arxiv_ids=["1706.03762v7"]`. When given an arXiv URL, extract the ID,
preserving any version suffix, and pass that ID to the tool. CI resolves
those exact papers, retaining a requested arXiv version (or recording the
current version for an unversioned ID), and records the requested identifier
in `metadata.json`. A lookup failure is reported without substituting a
search result; unavailable text stays visible with its reason. Once the
run completes, pull the branch and read the sources.

For topic searches:

1. **Write queries** yourself — 2-4 queries, each **1-4 keywords**:
   academic search backends match keywords, not sentences.
   Cover the topic's method, its task, and alternative phrasings.
2. **Explore**: `search_papers` (no key needed) to see which queries
   find what. Check `search_errors` per source instead of assuming every
   backend answered. The `airas_records` source is the research AIRAS
   itself produced whose gate passed — its rows list each claim with its
   verdict, so a `[refuted]` one shows what has already failed on the
   topic. The `airas_db` source is for finding papers only: its rows
   carry no PDF link, so they arrive without a text; query for the same
   title so the arXiv row brings it.
3. **Fetch** with `dispatch_literature_fetch`, passing the query and
   options you settled on (`sources` defaults to `arxiv,airas_records`,
   whose rows always yield a text). The repository's CI runs that search again,
   fetches each result's text from the search source's own `pdf_url`, and
   commits **every** result into `.research/sources/<id>/`
   (`metadata.json`, and `fulltext.txt` when a text was fetched) on the
   branch. Once `get_workflow_runs` reports the run completed, pull the
   branch. Repeat for each query; every fetch stays in the repository,
   cited or not.

Only CI writes `.research/sources/` — never add or edit a file there:
the gate compares every source new to main with its run's artifact.
`hypothesize-and-design` reads the sources and comes back to this skill
when the literature turns out thin.

**Output**: `.research/sources/<id>/` for every fetched result, on the
branch.
