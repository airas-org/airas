"""claims.tex: the paper's claim list is rendered from the record.

Deterministic from (record, metrics) alone, so the freeze commit carries it
with every outcome pending, and the same function regenerates it once the
runs are in.
"""

from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    LiteratureSource,
    Prediction,
    QuotedPassage,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.research_record.render.render_claims_tex import render_claims_tex
from airas.research_record.render.render_paper_values import (
    latex_text,
    render_values_tex,
)

SEYVAL = SeyvalVerifier(kind=VerifierKind.SEYVAL)


def _record(verdict: str | None = None) -> ResearchRecord:
    return ResearchRecord(
        hypotheses=[
            Hypothesis(
                id="h1",
                statement="Method X improves accuracy.",
                assumptions=["Accuracy on this dataset stands for the property (c1)."],
                claims=[
                    SeyvalClaim(
                        verifier=SEYVAL,
                        id="c1",
                        statement="X beats the baseline.",
                        rationale="Head-to-head on the hypothesis's own metric.",
                        verdict=verdict,
                        criterion=Criterion(
                            metric="accuracy",
                            subject="run_2",
                            reference="run_1",
                            op=">=",
                            margin=0.02,
                        ),
                        prediction=Prediction(low=0.02, high=0.04, basis="pilot"),
                        designs=[
                            SeyvalDesign(
                                id="d1",
                                runs=[
                                    SeyvalRun(run_id="run_1"),
                                    SeyvalRun(run_id="run_2"),
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )


def test_pending_before_any_run() -> None:
    tex = render_claims_tex(_record(), {})
    assert r"\textbf{Hypothesis 1.} Method X improves accuracy." in tex
    assert r"\item[\textbf{Claim 1}] X beats the baseline." in tex
    assert r"\emph{Rationale:} Head-to-head on the hypothesis's own metric." in tex
    assert r"\item Accuracy on this dataset stands for the property (c1)." in tex
    assert r"\texttt{\detokenize{run_2}}.\texttt{\detokenize{accuracy}} $-$" in tex
    assert r"$\geq 0.02$" in tex
    assert r"\emph{Prediction:} $[0.02, 0.04]$ (pilot)." in tex
    assert r"\emph{Observed:} pending." in tex
    assert r"\emph{Verdict:} pending." in tex


def test_observed_and_verdict_once_the_runs_are_in() -> None:
    metrics = {"run_1": {"accuracy": 0.871}, "run_2": {"accuracy": 0.902}}
    tex = render_claims_tex(_record("supported"), metrics)
    assert r"\emph{Observed:} 0.031." in tex
    assert r"\emph{Verdict:} supported." in tex


def test_an_unresolvable_metric_stays_pending() -> None:
    tex = render_claims_tex(_record(), {"run_1": {"f1": 0.5}, "run_2": {"f1": 0.6}})
    assert r"\emph{Observed:} pending." in tex


def test_record_text_is_escaped_for_pdflatex() -> None:
    """Prose is the author's; `_` `{` `%` in it must not become LaTeX, and a
    Lean statement's symbols must become math the engine has glyphs for."""
    assert latex_text("Method X improves accuracy.") == "Method X improves accuracy."
    assert (
        latex_text("sum_range_succ & 100% {ok}") == r"sum\_range\_succ \& 100\% \{ok\}"
    )
    assert (
        latex_text("∀ (n : ℕ), 2 * ∑ i ∈ Finset.range (n + 1), i = n²")
        == r"$\forall$ (n : $\mathbb{N}$), 2 * $\sum$ i $\in$ Finset.range (n + 1), i = n$^{2}$"
    )
    record = _record()
    record.hypotheses[0].claims[0].statement = "Σ_{i<n} (2i+1) = n²"
    assert r"\_" in render_claims_tex(record, {})
    from airas.core.types.map_record_to_publication import PaperValue

    tex = render_values_tex(
        [PaperValue(ref="t.params.statement", display="∀ n, n ≤ n")], None
    )
    assert "∀" not in tex and r"$\forall$ n, n $\leq$ n" in tex


def test_a_lean_claim_names_the_run_it_rests_on() -> None:
    from airas.core.types.research_record import (
        LeanClaim,
        LeanDesign,
        LeanParams,
        LeanResult,
        LeanRun,
        LeanVerifier,
    )

    run = LeanRun(
        run_id="gauss-sum",
        params=LeanParams(
            module="Airas.GaussSum", decl="gauss_sum_mul_two", statement="x"
        ),
    )
    claim = LeanClaim(
        id="c1",
        statement="The Gauss sum holds.",
        rationale="First instance.",
        verifier=LeanVerifier(kind=VerifierKind.LEAN),
        designs=[LeanDesign(id="d1", runs=[run])],
    )
    record = ResearchRecord(
        hypotheses=[Hypothesis(id="h1", statement="H.", claims=[claim])]
    )
    pending = render_claims_tex(record, {})
    assert r"\emph{Evidence:} run \texttt{\detokenize{gauss-sum}}, pending." in pending

    run.results.append(
        LeanResult(
            id="34941959631",
            commit="a" * 40,
            axioms=["propext"],
            statement_matches=True,
        )
    )
    realized = render_claims_tex(record, {})
    assert "execution \\texttt{\\detokenize{34941959631}}" in realized
    assert "commit \\texttt{\\detokenize{aaaaaaaaaaaa}}" in realized
    assert "axioms: \\texttt{\\detokenize{propext}}" in realized


def test_grounds_and_cited_passages_are_citations_of_their_source() -> None:
    """The paper cites the source as main.tex does (``cite[s1.p1]{key}``),
    so the link leads to the bibliography entry; the quotes stay in
    record.json and are not reprinted."""
    record = _record()
    record.literature.append(
        LiteratureSource(
            id="s1",
            title="Attention Is All You Need",
            year=2017,
            bibkey="vaswani-2017-attention",
            passages=[
                QuotedPassage(
                    id="s1.p1",
                    node_type="result",
                    anchor="table",
                    quote="We apply dropout & more.",
                ),
                QuotedPassage(id="s1.p2", node_type="setup", quote="Adam."),
            ],
        )
    )
    record.hypotheses[0].grounded_on = ["s1.p1"]
    claim = record.hypotheses[0].claims[0]
    claim.cites_passages = ["s1.p1"]
    claim.criterion.reference_passage = "s1.p1"
    claim.designs[0].cites_passages = ["s1.p2", "s9.p1"]
    tex = render_claims_tex(record, {})
    assert r"Method X improves accuracy.~\cite[s1.p1]{vaswani-2017-attention}" in tex
    assert (
        r"X beats the baseline.~\cite[s1.p1, s1.p2]{vaswani-2017-attention}, "
        r"\texttt{\detokenize{s9.p1}}" in tex
    )
    assert "Sources" not in tex and "dropout" not in tex
