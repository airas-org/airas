---
name: search-papers
description: Author search queries, search papers with the AIRAS MCP tools and download the full text of the promising ones. Use to bring literature on a topic to hand; reading and distilling it happens in hypothesize-and-design, which returns here whenever it needs more.
---

# Search papers

1. **Write queries** yourself — 2-4 queries, each **1-4 keywords**:
   academic search backends match keywords, not sentences.
   Cover the topic's method, its task, and alternative phrasings.
2. **Search**: `search_papers` (no key needed). Check `search_errors`
   per source instead of assuming every backend answered. The
   `airas_records` source is the research AIRAS itself produced whose
   gate passed: query it first with `verdict="refuted"` to learn what has
   already failed on the topic, and cite a study through its
   `external_ids.airas_record`. The `airas_db` source is for finding
   papers only: its rows carry no DOI or arXiv id, and `preregister_record`
   pins a paper by one of those, so look the identifier up (the same
   title on arXiv, or the venue's DOI) before you rely on such a row.
3. **Download** the promising rows with `fetch_paper_fulltext`, passing
   **both** `doi` and `pdf_url` when the row has both — a DOI alone
   often returns abstract-only. On `status="fulltext"` the whole text
   is in `fulltext_path` (under `~/.airas/cache/fulltext/`, pages
   separated by form feeds); nothing comes back inline. `abstract_only`
   returns the abstract and no file.

Nothing here touches the research repository or the record, and nothing
has to be read yet. Keep the search rows and each `fulltext_path`
together: `hypothesize-and-design` reads from them and comes back to
this skill when the literature turns out thin.

**Output**: search rows for the candidate papers, each with its
identifiers and `fulltext_path`.
