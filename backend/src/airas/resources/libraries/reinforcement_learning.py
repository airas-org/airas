# Reinforcement Learning libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
REINFORCEMENT_LEARNING_LIBRARIES: dict[str, dict[str, str | None]] = {
    "gymnasium": {
        "description": "Standard API and environments for reinforcement learning",
        "category": "reinforcement_learning",
        "official_docs": "https://gymnasium.farama.org",
        "github": "https://github.com/Farama-Foundation/Gymnasium",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pettingzoo": {
        "description": "Multi-agent reinforcement learning environments API",
        "category": "reinforcement_learning",
        "official_docs": "https://pettingzoo.farama.org",
        "github": "https://github.com/Farama-Foundation/PettingZoo",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "stable-baselines3": {
        "description": "Reliable PyTorch implementations of standard RL algorithms",
        "category": "reinforcement_learning",
        "official_docs": "https://stable-baselines3.readthedocs.io/en/master",
        "github": "https://github.com/DLR-RM/stable-baselines3",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "cleanrl": {
        "description": "Single-file, research-friendly RL algorithm implementations",
        "category": "reinforcement_learning",
        "official_docs": "https://docs.cleanrl.dev",
        "github": "https://github.com/vwxyzjn/cleanrl",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "torchrl": {
        "description": "PyTorch-native RL library (TensorDict-based)",
        "category": "reinforcement_learning",
        "official_docs": "https://docs.pytorch.org/rl",
        "github": "https://github.com/pytorch/rl",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
