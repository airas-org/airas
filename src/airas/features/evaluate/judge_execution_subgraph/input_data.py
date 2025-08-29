from airas.types.research_hypothesis import ExperimentalResults, ResearchHypothesis

judge_execution_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="""
Adaptive Curvature Momentum (ACM) Optimizer Overview Existing adaptive optimizers such as Adam and AdaBelief dynamically adjust the learning rate based on the history of gradients. However, while these methods adapt to the magnitude of the gradients, they do not fully exploit information about the local curvature of the loss landscape. In this proposal, we introduce a new optimizer called Adaptive Curvature Momentum (ACM), which utilizes local quadratic approximations to adaptively adjust the update direction and scale.
""",
        experimental_results=ExperimentalResults(
            result="Training completed successfully with ACM optimizer. Final metrics: accuracy=94.2%, loss=0.087, convergence_epochs=45. Comparison with baselines: ACM vs Adam (92.1%), ACM vs SGD (89.7%), ACM vs AdaBelief (93.5%). Memory usage: 2.1GB, Training time: 3.2 hours.",
            error="",
            was_experiment_executed=True,
            is_better_than_baseline=True,
        ),
    ),
    "executed_flag": True,
}
