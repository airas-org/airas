"""The canonical research record."""

from typing import Any

from airas.core.credentials import refresh_environment
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.mcp.app import mcp
from airas.mcp.context import (
    _arxiv_client,
    _async_session,
    _litellm_client,
    _search_index,
    _semantic_scholar_client,
)
from airas.usecases.hypothesis import declarations
from airas.usecases.literature import register_sources as register_sources_usecase
from airas.usecases.publication import judge_citations as judge_citations_usecase
from airas.usecases.publication import realize_paper_values


@mcp.tool()
async def preregister_record(
    local_path: str,
    hypotheses: list[dict[str, Any]],
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Create the research record before any experiment has run.

    Writes `.research/record.json` — the canonical record the whole
    verification system keys on — and commits it in the same step
    (`freeze_commit` in the result). That commit is the freeze point: every
    later revision must *contain* this one whole, so a claim cannot be
    reworded, its criterion cannot be moved, a run's conditions cannot be
    changed and a result cannot be dropped once written.

    The record is a tree, read as "to support this hypothesis, these claims;
    to verify this claim, these designs; a design is these runs":

      hypotheses: [{
        "id": "h1", "statement": "the hypothesis, in prose",
        "assumptions": ["what must be granted for the claims together to "
                        "imply h1, naming the claims concerned", ...],
        "claims": [{
          "id": "c1", "statement": "one assertive sentence",
          "rationale": "why c1 holding is evidence for h1, and for which part",
          "verifier": {"kind": "seyval"},
          "criterion": {"metric": "accuracy", "subject": "proposed-...",
                        "reference": "comparative-1-...", "op": ">=",
                        "margin": 0.02},
          "prediction": {"low": 0.02, "high": 0.04, "basis": "pilot run"},
          "designs": [{
            "id": "d1", "summary": "...",
            "runs": [{"run_id": "proposed-...", "description": "...",
                      "params": {"mode": "full"}}]
          }]
        }],
        "tables": [...], "charts": [...], "notes": [...]
      }]

    A hypothesis's `grounded_on`, a claim's, design's or run's
    `cites_passages` and a criterion's `reference_passage` name passages of
    the literature registered earlier with `register_sources` (`"s1.p2"`):
    what the declaration rests on, in the prior work's own words. The gate
    refuses a passage no source declares, and one registered after the
    declaration that names it.

    `run_id` names the results directory the run will produce and must be
    unique across the whole record — a run belongs to exactly one claim.
    (Not a bare number: `criterion.reference` reads a number as a constant.)

    The claims are meant to imply the hypothesis together (c1 ∧ … ∧ cn ⇒
    h1). `rationale` says why each claim is a member of that set; the
    hypothesis's `assumptions` say what has to be granted for the
    conjunction to reach h1 — a proxy metric standing for the property,
    generalisation beyond the datasets run, and the like. Every claim
    supported leaves exactly the assumptions unverified, so they are what
    the paper states as such; claims.tex lists them under the claims.

    `verifier` says what verifies the claim and sets its `verified` and
    `verdict`; one per claim (a claim needing both a proof and an experiment
    is two claims), and required. The kind decides what `params` declares
    and what the gate re-derives:

      seyval    (experiment) params = dispatch conditions, e.g. {"mode":
                "full"}, checked against what the platform recorded.
                `criterion` is the falsification line, required:
                (subject.metric - reference) op margin, where reference is
                a run under this claim (its same metric) or a constant;
                exactly at the margin counts as met. `prediction` is the
                interval the difference is expected to land in, required,
                a range never a point, with where it comes from. Verdict:
                supported/refuted by the criterion on the runs' metrics;
                inconclusive when the metric cannot be resolved.
      lean      (theory) {"kind": "lean", "toolchain": "leanprover/lean4:
                v4.33.1", "mathlib_rev": "<sha>", "allowed_axioms": [...]};
                params = {"module": "Airas.Thm1", "decl": "thm1",
                "statement": "<the type `#check @thm1` prints>"}. The
                toolchain and mathlib_rev are the repository's
                `lean/lean-toolchain` and `lean/lake-manifest.json`. The run
                is dispatched like an experiment (`dispatch_experiment` with
                a `config/run/<run_id>.yaml` holding kind: lean, module,
                decl) and writes `lean.json` into its results directory.
                Verdict: supported iff the result has no errors (build
                failed, sorry, statement drift, module/decl/toolchain/
                mathlib_rev other than declared, an axiom outside
                allowed_axioms); else inconclusive — Lean cannot refute.
      llm_judge (qualitative) {"kind": "llm_judge", "model": "<dated id>",
                "rubric": "<repo path>", "temperature": 0, "samples": 5};
                params = {"evidence": ["<repo paths>"]}. The judgment
                writes `judgment.json` into the run's results directory.
                It verifies that the evidence presented supports the
                claim, not that the evidence is true.
    The tool that executes llm_judge, and the gate's re-execution of lean
    and llm_judge, are not implemented yet.

    Also renders `claims.tex` — the numbered claim list with each criterion,
    prediction and (pending) verdict — into `.research/latex/{template}/`
    and commits it with the record; `\\input{claims.tex}` where the paper
    lists its claims. The gate regenerates and diffs it at every stage.

    Fails if record.json already holds declarations (use `append_to_record`;
    the empty record a repository ships is initialised in place), if a claim
    declares no run, if a seyval claim lacks its criterion or prediction, or
    if the clone cannot commit. After this: write every future experimental
    number in main.tex as `\\airasval{<run_id>.<metric>}` or
    `\\airasval{<run_id>.params.<key>}`, compile, commit main.tex and push
    to the staging ref — tell the user the freeze sha once it lands.
    """
    return await declarations.preregister_record(
        local_path, hypotheses, latex_template_name
    )


@mcp.tool()
async def append_to_record(
    local_path: str,
    hypotheses: list[dict[str, Any]] | None = None,
    hypothesis_id: str | None = None,
    claims: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
    charts: list[dict[str, Any]] | None = None,
    notes: list[str] | None = None,
    source_id: str | None = None,
    passages: list[dict[str, Any]] | None = None,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Add declarations to the record; nothing already in it ever changes.

    The record only grows: every committed revision must contain the one
    before it whole, so this tool appends and never edits. `hypotheses`
    appends whole new hypotheses; `claims`, `tables`, `charts` and `notes`
    append under the hypothesis named by `hypothesis_id`. Entry shapes are
    the ones `preregister_record` documents.

    Revising a frozen entry means appending a new one with the *same id* —
    the later entry is the live one and the earlier stays readable in place.
    That is also how a design or a run is added to an existing claim: append
    the claim again, with the extra design.

    Use this for exploratory extensions (declare the claim and its runs
    first, then execute — results for an undeclared run fail verification).
    The append is committed in the same step (`commit` in the result);
    anything a run should count as evidence for must be in that commit's
    history before the run executes, so a claim declared after its run stays
    unverified forever. A seyval claim appended here needs its criterion and
    prediction like one preregistered; `claims.tex` is re-rendered and
    committed alongside.

    `passages` append under the source named by `source_id` (shape as in
    `register_sources`: `{"node_type", "quote", "anchor"?}`); the
    quote must be copied from that source's `fulltext.txt`, or the append is
    refused.
    """
    return await declarations.append_to_record(
        local_path,
        hypotheses=hypotheses,
        hypothesis_id=hypothesis_id,
        claims=claims,
        tables=tables,
        charts=charts,
        notes=notes,
        source_id=source_id,
        passages=passages,
        latex_template_name=latex_template_name,
    )


@mcp.tool()
async def register_sources(
    local_path: str,
    papers: list[dict[str, Any]] | None = None,
    repositories: list[dict[str, Any]] | None = None,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Pin the papers and repositories the research draws on, so their
    passages can be cited.

    A source is an entry of `.research/record.json`'s `literature`, pinned
    by a fulltext snapshot (`.research/sources/<id>/fulltext.txt`, pages
    separated by a form feed) whose sha256 the record holds. Each
    `papers[]` entry is one paper:

      {"airas_db": "<id from search_papers>"}            metadata from the db
      {"title", "authors", "year", "venue", "pdf_url",   what a web search found
       "doi"?, "arxiv_id"?, "url"?}
      + optional "passages": [{"node_type": "claim|result|method|setup|gap|
        definition", "anchor": "text|table|figure", "quote": "..."}]

    Whatever the origin, the same checks run: the paper must be confirmed
    by the registry behind an identifier it carries (airas-papers-db for
    `airas_db`, doi.org for `doi`, the arXiv API for `arxiv_id` — so a
    paper with none of the three cannot be registered), and its PDF must
    yield text (resolved from `arxiv_id`/`doi` the way `fetch_paper_fulltext`
    does, or from `pdf_url`). The tool writes the snapshot, sets the bibkey
    (`<surname>-<year>-<word>`, the key `\\cite` uses), renders
    `.research/latex/<template>/references.bib` from the record's literature
    (the gate regenerates it, so never edit it by hand) and commits record,
    snapshots and bibliography together; a paper that fails a check is
    refused and nothing is written. A paper already in the record (same DOI, arXiv id
    or URL) is left as it is.

    `repositories[]` pins code the research builds on: `{"url", "commit",
    "files": ["src/model.py", ...], "passages"?}`. The files are read at
    that commit into the snapshot (one page per file, headed `==> path <==`)
    and the fetch succeeding is the existence check (`verified_by: "git"`);
    a passage of a repository quotes lines of a file, with `"anchor":
    "code"`.

    Quotes are copied from the snapshot, not from the PDF: the gate checks
    that every passage's `quote` is verbatim in `fulltext.txt` (ligatures,
    line breaks and soft hyphens aside). Read the snapshot, declare
    passages here or with
    `append_to_record(source_id=..., passages=[...])`, then name them in a
    hypothesis's `grounded_on`, a claim's, design's or run's
    `cites_passages`, or a criterion's `reference_passage`.
    """
    refresh_environment()
    return await register_sources_usecase.register_sources(
        local_path,
        papers,
        repositories,
        latex_template_name,
        search_index=_search_index,
        arxiv_client=_arxiv_client(),
        semantic_scholar_client=_semantic_scholar_client(),
        http=_async_session,
    )


@mcp.tool()
async def update_record(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Realize the record from the run outputs and commit it.

    This is the only sanctioned way experimental numbers enter the paper.
    The declarations live in `.research/record.json`; this tool reads the
    actual run outputs in the local clone (`.research/results/<run_id>/` —
    metrics.json, eval_inputs/, evaluation/) and the provenance manifest
    `.provenance.json`, and appends to each run a `results[]` entry: the
    platform's execution id and commit, the hash of the evaluation inputs,
    the evaluator's report, and the metrics file verbatim. Numbers cannot
    be passed in, so a value that was never measured cannot enter the
    record.

    A lean run is read from `lean.json` and an llm_judge run from
    `judgment.json` in the same results directory.

    A claim's `verified` is set to true when every run under it has
    results — the data the claim rests on is in — and its `verdict` once
    the verifier concludes: for seyval, the declared criterion applied to
    the runs' metrics. Both
    are written once and never back; a re-run that would flip the verdict
    is reported by the gate as drift, and re-judging means appending the
    claim again under the same id. Whether the claim was declared before
    its runs executed is not modelled yet.

    It then renders `values.tex`, `tables/<key>.tex` and `claims.tex` into
    `.research/latex/{template}/`; when the clone has an `origin` remote,
    every value macro is a hyperlink to record.json at the commit that
    wrote it.

    This tool does not judge the result, and deliberately so. Whatever it
    reported locally, the agent could push regardless, so a local verdict
    was advice rather than a gate — and running the identical checks twice
    made the advisory pass look like a second, independent opinion. The
    verdict comes from CI, on the pushed commit, where the agent cannot
    intervene: push to the staging ref, read the run, and fast-forward the
    protected branch only when it is green.

    Then `\\input{values.tex}` in main.tex's preamble,
    `\\input{tables/<key>.tex}` where each table belongs, and every
    experimental number as `\\airasval{key}` — never a literal. A
    legitimate number no declaration can produce (e.g. a value quoted
    from a cited paper) must be wrapped as `\\unverified{...}` so it is
    surfaced for review.
    """
    refresh_environment()
    return await realize_paper_values.realize_paper_values(
        local_path, latex_template_name
    )


@mcp.tool()
async def judge_citations(
    local_path: str,
    model: str,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Have a model read every citation of a passage against the passage,
    and write its judgments into the record.

    The gate checks that a quote is verbatim and that `\\cite[s1.p2]{key}`
    points at a passage of that source; whether the citing text says what
    the passage says is a reading, and this asks `model` for it. Each place
    a passage is cited — the paragraph around a `\\cite[s1.p2]{key}` in
    main.tex, a claim's statement and rationale for its `cites_passages`, a
    hypothesis's statement for its `grounded_on` — is read against the
    quote in its snapshot context, so a quote clipped of its negation is
    seen with the negation. The judgment (model, supported, reason and a
    hash of the citing text) is appended to the passage in record.json
    and committed with claims.tex. A citing text already
    judged is not read again; a rewritten one is.

    `verify_paper_values` then reports, without a model call, the
    citations judged unsupported (`unsupported_citations`) and those the
    judgments do not cover (`unjudged_citations`) — review input like
    `unverified`, not failures. Run it after the paper is written and
    again after any rewrite. Requires an LLM provider key.
    """
    refresh_environment()
    return await judge_citations_usecase.judge_citations(
        local_path, model, latex_template_name, litellm_client=_litellm_client()
    )
