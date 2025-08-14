from airas.types.research_hypothesis import (
    ExperimentalDesign,
    ExperimentalResults,
    ResearchHypothesis,
)

analytic_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="Q-Denoising Diffusion Probe (QD²P) - a method that uses a lightweight, linear Q-probe to guide diffusion denoising process.",
        experimental_design=ExperimentalDesign(
            experiment_strategy="Experimental plan with three concrete experiments using PyTorch, NumPy, and visualization tools.",
            experiment_code="Python implementation of QD²P experiments comparing against baseline diffusion methods.",
        ),
        experimental_results=ExperimentalResults(
            result="QD²P shows quality improvement and 6.30x speedup from distillation with 100% quality retention."
        ),
    )
}
