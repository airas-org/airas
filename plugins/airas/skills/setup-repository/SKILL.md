---
name: setup-repository
description: Create an AIRAS experiment repository from the template and clone it — the repository that will hold all research state from here on. Use to set up the repository for a research project.
---

# Set up the experiment repository

1. `prepare_repository` — pass the visibility settled at the start of
   the flow (`is_private` defaults to true); returns `clone_url`;
   clone it locally with git. Requires `GH_PERSONAL_ACCESS_TOKEN`
   (`~/.airas/credentials.json`, editable via `open_dashboard`) with
   admin rights on the repository.

   It also provisions the Actions secrets and protects `main` in the
   same call. Both matter more than they look. Without
   `SEYVAL_API_KEY` the provenance cross-check **degrades to a skip
   rather than a failure**, so an unprovisioned repository looks like
   it is passing. Without branch protection, a red CI run can simply
   be pushed past, and every guarantee in the record becomes advisory.

2. **Read `warnings`, `secrets_set` and `branch_protected` in the
   result.** Neither failure aborts the creation, so a repository can
   come back usable and unenforced. If `branch_protected` is false,
   say so to the user rather than continuing as though the record were
   protected; `set_github_actions_secrets` and `protect_branch` fix
   each independently.

3. **Work through a staging ref, not by pushing to `main`.** A commit
   reaches the protected branch only once the record gate is green on
   that exact sha, and the check cannot run on a commit nobody has
   pushed. So push local `main` to a scratch ref, wait for the gate,
   then fast-forward:

   ```
   git push origin main:verify    # the gate runs on this sha
   # green
   git push origin main:main      # the same sha, fast-forwarded
   ```

   No local branch is needed — required checks are evaluated per
   commit, not per branch. Never squash or rebase to get a commit onto
   `main`: both rewrite commits, and verification asks whether each
   run's recorded commit is an ancestor of HEAD.

4. Look over the clone: the `.github/` workflows, `Makefile` and empty
   `src/` stubs are what the experiment code will be held to. The
   contract itself — run-id naming, CLI shape, sanity/pilot/full
   semantics, the files you may touch — is stated in
   `write-experiment-code`, not in the repository.
5. The repository is the home of all research state. Artifacts
   produced from here on (hypothesis, design, declarations, results)
   are committed here as they are made — `.research/research_history.json`
   ships empty and the repository's own workflows read the research
   context from it, so commit context there as soon as it exists
   (`upload_research_history` commits it against the pushed branch).
   If a hypothesis and design already exist, commit them now.

**Output**: a pushed clone, ready to receive research state, from
which a fresh session can continue without this conversation.
