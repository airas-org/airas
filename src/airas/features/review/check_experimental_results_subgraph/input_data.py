from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ExperimentalDesign, ResearchHypothesis

check_experimental_results_subgraph_input_data = {
    "paper_content": PaperContent(
        title="Test Paper Title",
        abstract="This is a test abstract. The experiment was executed and showed results better than baseline.",
        introduction="Introduction section.",
        related_work="Related work section: Previous studies include X and Y.",
        background="Background section: This research builds upon Z.",
        method="Method section.",
        experimental_setup="Experimental setup details.",
        results="Results section: Our method achieved 90% accuracy, which is 5% higher than the baseline of 85%.",
        conclusion="Conclusion section.",
    ),
    "new_method": ResearchHypothesis(
        method="A novel approach to improve accuracy.",
        experimental_design=ExperimentalDesign(
            experiment_strategy="Strategy A",
            experiment_details="Details of experiment A",
            experiment_code="print('hello world')",
        ),
        experimental_results=None,
        experimental_analysis=None,
    ),
}
