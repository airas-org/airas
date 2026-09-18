"""The fixed workflow: the research flow as a graph.

This package is the only place a `StateGraph` belongs. Everything under
`usecases/` is plain async functions; a node here calls one and returns
what the flow needs to remember. A subgraph is warranted only where the
control structure *is* the work — a polling loop, a retry cycle — and
today the one example lives in `infra/github/poll_github_actions_subgraph`.

**The same steps the agent runs.** `plugins/airas/skills/auto-research/`
states this flow in prose for an agent to follow; this package states it
in edges for a graph to execute. Both call the same functions, so the two
must not grow separate implementations. Where the agent uses its own
judgement — authoring queries, distilling a paper, choosing which
passages to quote — a node here calls the backend LLM through the
step's usecase, whose prompt and context functions are the *same* ones
`get_prompts` hands the agent (#1054).

**State is the repository.** The graph state carries a pointer and a few
derived facts, not the research itself:

    class ResearchFlowState(TypedDict):
        github_config: GitHubConfig
        local_path: str        # the clone; `.research/record.json` lives here
        freeze_commit: str     # what preregistration returned

`ResearchRecord` does not go in the state. Its authority comes from being
committed — the gate walks every revision in git history — so an
in-memory copy would be a second, unverifiable truth. Each usecase loads
the record, changes it, saves and commits it; a node just names the path.
A fresh session must be able to resume from the clone alone.

**Order is an invariant, not a convention.** Nothing is dispatched before
the freeze commit exists, so the paper is written *before* the experiment
runs:

    setup_repository → search_papers → fetch_paper_fulltext
      → generate_hypothesis → generate_design
      → preregister_record(literature, hypotheses)   ← the freeze commit
      → write_experiment_code
      → dispatch_experiment → import_run_outputs
      → analyze_results
      → update_record → verify → publish

The graphs in `usecases/autonomous_research/` predate this model and run
experiments before writing the paper. They are not the starting point for
this package; they are what it replaces.

**Still missing.** The record reaches GitHub only through the agent's own
`git push`. A graph has no shell, so a push in `infra/local_git.py` is a
prerequisite for anything here to publish a result.
"""
