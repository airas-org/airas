writer_subgraph_input_data = {
    "research_hypothesis": {
        "method": "We propose a novel approach that combines transformer attention mechanisms with reinforcement learning to improve decision-making in dynamic environments. Our method leverages multi-head attention to capture temporal dependencies and uses policy gradient methods for optimization.",
        "experimental_design": {
            "verification_policy": "We compare our method against state-of-the-art baselines using standard benchmarks including Atari games and continuous control tasks. Performance is measured using average cumulative reward over 100 episodes.",
            "experiment_details": "Experiments are conducted on 5 different environments with 3 random seeds each. Training runs for 1M timesteps with evaluation every 10K steps. We use Adam optimizer with learning rate 3e-4 and batch size 256.",
            "experiment_code": """
def train_agent(env, model, num_timesteps=1000000):
    optimizer = Adam(model.parameters(), lr=3e-4)
    for step in range(num_timesteps):
        state = env.reset()
        episode_reward = 0
        while not done:
            action = model.select_action(state)
            next_state, reward, done, _ = env.step(action)
            model.update(state, action, reward, next_state)
            state = next_state
            episode_reward += reward
        if step % 10000 == 0:
            evaluate_model(model, env)
""",
        },
        "experimental_information": {
            "result": "Our method achieves 15% higher average reward compared to the best baseline (PPO) across all environments. Specifically, we obtain 520+/-25 points on Breakout, 1840+/-67 points on SpaceInvaders, and 95+/-8 points on CartPole.",
            "error": None,
            "image_file_name_list": [
                "training_curves.pdf",
                "attention_visualization.pdf",
                "performance_comparison.pdf",
            ],
            "notes": "Training was stable across all seeds. Attention weights show clear temporal patterns. Method scales well to larger environments.",
        },
        "experimental_analysis": {
            "analysis_report": "The results demonstrate that our attention-based approach successfully captures temporal dependencies that are crucial for decision-making. The attention visualization reveals that the model learns to focus on relevant past states when making decisions. Ablation studies show that both the attention mechanism and RL components are necessary for optimal performance. The method shows consistent improvements across different environment types, suggesting good generalization capabilities.",
        },
    },
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
