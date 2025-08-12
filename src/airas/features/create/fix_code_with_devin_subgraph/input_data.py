from airas.types.devin import DevinInfo
from airas.types.research_hypothesis import ExperimentalResults, ResearchHypothesis

fix_code_with_devin_subgraph_input_data = {
    "devin_info": DevinInfo(
        session_id="3dfb2fb5b1304e568aacfb0c79f8caba",
        devin_url="https://app.devin.ai/sessions/3dfb2fb5b1304e568aacfb0c79f8caba",
    ),
    "new_method": ResearchHypothesis(
        method="We propose a novel approach for automated machine learning pipeline optimization that combines reinforcement learning with neural architecture search.",
        experimental_results=ExperimentalResults(
            result="Process completed with warnings. Accuracy: 0.85",
            error="Warning: Some packages have compatibility issues. ImportError: No module named 'torch_geometric'",
            image_file_name_list=["results_plot.png", "accuracy_curve.png"],
            notes="Experiment completed but with some dependency issues that need fixing.",
        ),
    ),
    "executed_flag": True,
}
