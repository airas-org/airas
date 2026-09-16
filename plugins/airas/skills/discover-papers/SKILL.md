---
name: discover-papers
description: Author search queries, search and read papers with the AIRAS MCP tools, and distill them into a research_study_list. Use for a literature survey or to ground a research topic in prior work.
---

# Discover papers

1. **Write queries** yourself — 2-4 queries, each **1-4 keywords**: 
   academic search backends match keywords, not sentences.
   Cover the topic's method, its task, and alternative phrasings.
2. **Search**: `search_papers` (no key needed). Check `search_errors`
   per source instead of assuming every backend answered. The
   `airas_records` source is the research AIRAS itself produced whose
   gate passed: query it first with `verdict="refuted"` to learn what has
   already failed on the topic, and cite a study through its
   `external_ids.airas_record`.
3. **Read**: `fetch_paper_fulltext`, passing **both** `doi` and
   `pdf_url` when the search row has both — a DOI alone often returns
   abstract-only. Check `status`: `abstract_only` means you are about
   to write about a paper you only skimmed; say so or read elsewhere.
   Keep `max_chars` at its default unless one paper must be read in full.
4. **Distill** each paper into a `ResearchStudy` entry yourself. The
   shape shares no key names with `search_papers` rows: `authors`,
   `citations`, `arxiv_id` go under `meta_data`; only `title` is
   required, so `{"title", "abstract"}` is valid for a paper you did
   not fully read. Call `get_input_schema` before building by hand.
5. **Register what the research will rest on** with `register_sources`
   (needs the local clone). Pass an `airas_db` id from the search row,
   or `doi` / `arxiv_id` with the title, authors, year, venue and
   `pdf_url` you found — a paper with none of the three identifiers
   cannot be registered, because nothing can confirm it exists. The
   tool pins each paper by a fulltext snapshot
   (`.research/sources/<id>/fulltext.txt`) and writes
   `references.bib`. Then read the snapshot and declare the passages
   the research draws on — `append_to_record(source_id="s1",
   passages=[{"node_type": "gap|claim|result|method|setup|definition",
   "quote": "<copied verbatim from fulltext.txt>"}])`. The gate checks
   every quote against the snapshot, so copy, never retype.

**Output**: a `research_study_list`, and registered sources with
passage ids (`s1.p2`) for `hypothesize-and-design` to name.
