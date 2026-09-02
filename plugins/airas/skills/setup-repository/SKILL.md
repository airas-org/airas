---
name: setup-repository
description: Create an AIRAS experiment repository from the template and clone it — the repository that will hold all research state from here on. Use to set up the repository for a research project.
---

# Set up the experiment repository

1. `prepare_repository` — pass the visibility settled at the start of
   the flow (`is_private` defaults to true); returns `clone_url`;
   clone it locally with git. Requires `GH_PERSONAL_ACCESS_TOKEN`
   (`~/.airas/credentials.json`, editable via `open_dashboard`).
2. Read the repository's `AGENTS.md` — it is the contract the runners
   hold you to (run-id naming, CLI shape, sanity/pilot/full
   semantics), and everything written into this repository later is
   held to it.
3. The repository is the home of all research state. Artifacts
   produced from here on (hypothesis, design, declarations, results)
   are committed here as they are made — `.research/research_history.json`
   ships empty and the repository's own workflows read the research
   context from it, so commit context there as soon as it exists
   (`upload_research_history` commits it against the pushed branch).
   If a hypothesis and design already exist, commit them now.

**Output**: a pushed clone, ready to receive research state, from
which a fresh session can continue without this conversation.
