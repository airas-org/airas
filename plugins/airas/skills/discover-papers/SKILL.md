---
name: discover-papers
description: Author search queries, search and read papers with the AIRAS MCP tools, and distill them into a research_study_list. Use for a literature survey or to ground a research topic in prior work.
---

# Discover papers

1. **Write queries** yourself — 2-4 queries, each **1-4 keywords**: 
   academic search backends match keywords, not sentences.
   Cover the topic's method, its task, and alternative phrasings.
2. **Search**: `search_papers` (no key needed). Check `search_errors`
   per source instead of assuming every backend answered.
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

**Output**: a `research_study_list`.
