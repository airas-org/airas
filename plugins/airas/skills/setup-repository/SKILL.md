---
name: setup-repository
description: Create an AIRAS experiment repository from the template and clone it — the repository that will hold all research state from here on. Use to set up the repository for a research project.
---

# Set up the experiment repository

1. `prepare_repository` — pass the visibility settled at the start of
   the flow: **`is_private=False`** unless the user asked for private,
   because on GitHub's free plan branch protection (step 2 below) is
   only available on public repositories; returns `clone_url`;
   clone it locally with git. Requires `GH_PERSONAL_ACCESS_TOKEN`
   (`~/.airas/credentials.json`) with
   admin rights on the repository.

   It also protects `main` in the same call. Without branch
   protection, a red CI run can simply be pushed past, and every
   guarantee in the record becomes advisory.

2. **Read `warnings` and `branch_protected` in the result.** A failed
   protection does not abort the creation, so a repository can come
   back usable and unenforced. If `branch_protected` is false, say so
   to the user rather than continuing as though the record were
   protected. The repair is to run `prepare_repository` again once the
   cause is fixed (admin rights, a public repository): it is safe on the
   repository it already created and redoes only what is missing.

3. `set_github_actions_secrets` — copies this machine's API keys into
   the repository's Actions secrets. Without `SEYVAL_API_KEY` there,
   the provenance cross-check **degrades to a skip rather than a
   failure**, so an unprovisioned repository looks like it is passing.
   Run it again whenever a key is added or rotated.

4. **Work through a staging ref, not by pushing to `main`.** A commit
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

5. Look over the clone: the `.github/` workflows, `Makefile` and empty
   `src/` stubs are what the experiment code will be held to. The
   contract itself — run-id naming, CLI shape, sanity/pilot/full
   semantics, the files you may touch — is stated in
   `write-experiment-code`, not in the repository.
6. The repository is the home of all research state. Everything
   produced from here on (sources, hypothesis, declarations, results)
   goes into `.research/record.json` through the record tools and is
   committed as it is made, so a fresh session restores from the clone
   alone.

**Output**: a pushed clone, ready to receive research state, from
which a fresh session can continue without this conversation.
