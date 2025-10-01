from airas.types.research_hypothesis import (
    Experiment,
    ExperimentalAnalysis,
    ExperimentalDesign,
    ExperimentalResults,
    ExperimentEvaluation,
    ResearchHypothesis,
)
from airas.types.research_study import LLMExtractedInfo, MetaData, ResearchStudy

writer_subgraph_input_data = {
    "new_method": ResearchHypothesis(
        method="We propose a novel approach that combines transformer attention mechanisms with reinforcement learning to improve decision-making in dynamic environments. Our method leverages multi-head attention to capture temporal dependencies and uses policy gradient methods for optimization.",
        experimental_design=ExperimentalDesign(
            experiment_strategy="We compare our method against state-of-the-art baselines using standard benchmarks including Atari games and continuous control tasks. Performance is measured using average cumulative reward over 100 episodes.",
            experiments=[
                Experiment(
                    experiment_id="exp-1",
                    description="Baseline comparison on Atari games",
                    run_variations=[
                        "baseline_ppo",
                        "baseline_a2c",
                        "proposed_attention_rl",
                    ],
                    results=ExperimentalResults(
                        result="Our method achieves 15% higher average reward compared to PPO. Breakout: 520+/-25 points, SpaceInvaders: 1840+/-67 points.",
                        image_file_name_list=[
                            "training_curves.pdf",
                            "attention_visualization.pdf",
                        ],
                    ),
                    evaluation=ExperimentEvaluation(
                        consistency_score=9,
                        consistency_feedback="Excellent experimental design with clear statistical validation.",
                        is_selected_for_paper=True,
                    ),
                ),
                Experiment(
                    experiment_id="exp-2",
                    description="Continuous control tasks (CartPole, MountainCar)",
                    run_variations=["baseline_ddpg", "proposed_attention_rl"],
                    results=ExperimentalResults(
                        result="CartPole: 95+/-8 points vs DDPG 78+/-12. Method shows consistent improvements.",
                        image_file_name_list=["performance_comparison.pdf"],
                    ),
                    evaluation=ExperimentEvaluation(
                        consistency_score=8,
                        consistency_feedback="Strong evidence with good generalization across tasks.",
                        is_selected_for_paper=True,
                    ),
                ),
            ],
        ),
        experimental_analysis=ExperimentalAnalysis(
            analysis_report="The results demonstrate that our attention-based approach successfully captures temporal dependencies that are crucial for decision-making. The attention visualization reveals that the model learns to focus on relevant past states when making decisions. Ablation studies show that both the attention mechanism and RL components are necessary for optimal performance. The method shows consistent improvements across different environment types, suggesting good generalization capabilities."
        ),
    ),
    "research_study_list": [
        ResearchStudy(
            title="Attention Is All You Need",
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism.",
            meta_data=MetaData(
                arxiv_id="1706.03762",
                doi="10.48550/arXiv.1706.03762",
                authors=["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki"],
                published_date="2017",
                venue="Advances in Neural Information Processing Systems",
                volume="30",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Introduced the Transformer architecture based solely on attention mechanisms",
                methodology="Multi-head self-attention mechanism with positional encoding",
                experimental_setup="Machine translation tasks on WMT datasets",
                limitations="Requires large amounts of training data",
                future_research_directions="Applications to other modalities and efficiency improvements",
            ),
        ),
        ResearchStudy(
            title="Proximal Policy Optimization Algorithms",
            abstract="We propose a new family of policy gradient methods for reinforcement learning, which alternate between sampling data through interaction with the environment, and optimizing a surrogate objective function using stochastic gradient ascent.",
            meta_data=MetaData(
                arxiv_id="1707.06347",
                authors=["Schulman, John", "Wolski, Filip", "Dhariwal, Prafulla"],
                published_date="2017",
                venue="arXiv preprint",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Proximal Policy Optimization (PPO) algorithm for stable policy gradient learning",
                methodology="Clipped surrogate objective function with trust region constraints",
                experimental_setup="Atari games and continuous control tasks",
                limitations="Hyperparameter sensitivity and sample efficiency",
                future_research_directions="Integration with other RL techniques and theoretical analysis",
            ),
        ),
    ],
    "reference_research_study_list": [
        ResearchStudy(
            title="Human-level control through deep reinforcement learning",
            abstract="We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input using reinforcement learning.",
            meta_data=MetaData(
                authors=["Mnih, Volodymyr", "Kavukcuoglu, Koray", "Silver, David"],
                published_date="2015",
                venue="Nature",
                volume="518",
                pages="529--533",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Deep Q-Network (DQN) for learning from raw pixels",
                methodology="Convolutional neural networks with experience replay",
                experimental_setup="Atari 2600 games benchmark",
                limitations="Overestimation bias and sample efficiency",
                future_research_directions="Improved architectures and training stability",
            ),
        )
    ],
    "references_bib": """% ===========================================
% REQUIRED CITATIONS
% These papers must be cited in the manuscript
% ===========================================

@article{ashish_2017_attention,
 abstract = {The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism.},
 arxiv_url = {https://arxiv.org/abs/1706.03762},
 author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki},
 doi = {10.48550/arXiv.1706.03762},
 journal = {Advances in Neural Information Processing Systems},
 title = {Attention Is All You Need},
 volume = {30},
 year = {2017}
}

@article{schulman_2017_ppo,
 abstract = {We propose a new family of policy gradient methods for reinforcement learning, which alternate between sampling data through interaction with the environment, and optimizing a surrogate objective function using stochastic gradient ascent.},
 arxiv_url = {https://arxiv.org/abs/1707.06347},
 author = {Schulman, John and Wolski, Filip and Dhariwal, Prafulla},
 journal = {arXiv preprint arXiv:1707.06347},
 title = {Proximal Policy Optimization Algorithms},
 year = {2017}
}

% ===========================================
% REFERENCE CANDIDATES
% Additional reference papers for context
% ===========================================

@article{mnih_2015_dqn,
 abstract = {We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input using reinforcement learning.},
 author = {Mnih, Volodymyr and Kavukcuoglu, Koray and Silver, David},
 journal = {Nature},
 pages = {529--533},
 title = {Human-level control through deep reinforcement learning},
 volume = {518},
 year = {2015}
}""",
}
