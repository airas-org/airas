---
name: search-papers
description: Author search queries, explore them with the AIRAS MCP tools and have the repository's CI fetch every result into .research/sources/. Use to bring literature on a topic to hand; reading and distilling it happens in hypothesize-and-design, which returns here whenever it needs more.
---

# Search papers

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
   options you settled on. The repository's CI runs that search again,
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
