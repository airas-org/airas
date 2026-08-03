# reinforcement_learning / simulation documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
SIMULATION_LIBRARIES: dict[str, dict[str, str | None]] = {
    "mujoco": {
        "description": "Physics engine for robotics and biomechanics simulation",
        "domain": "reinforcement_learning",
        "category": "simulation",
        "official_docs": "https://mujoco.readthedocs.io/en/stable",
        "github": "https://github.com/google-deepmind/mujoco",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "isaac-lab": {
        "description": "GPU-parallel robot learning framework on Isaac Sim",
        "domain": "reinforcement_learning",
        "category": "simulation",
        "official_docs": "https://isaac-sim.github.io/IsaacLab",
        "github": "https://github.com/isaac-sim/IsaacLab",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pybullet": {
        "description": "Python physics simulation for robotics and RL",
        "domain": "reinforcement_learning",
        "category": "simulation",
        "official_docs": "https://pybullet.org",
        "github": "https://github.com/bulletphysics/bullet3",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "brax": {
        "description": "Differentiable JAX-based physics engine for RL at scale",
        "domain": "reinforcement_learning",
        "category": "simulation",
        "official_docs": "https://github.com/google/brax",
        "github": "https://github.com/google/brax",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "dm-control": {
        "description": "DeepMind control suite and MuJoCo-based RL environments",
        "domain": "reinforcement_learning",
        "category": "simulation",
        "official_docs": "https://github.com/google-deepmind/dm_control",
        "github": "https://github.com/google-deepmind/dm_control",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "maniskill": {
        "description": "GPU-parallelized robot manipulation benchmark and simulator",
        "domain": "reinforcement_learning",
        "category": "simulation",
        "official_docs": "https://maniskill.readthedocs.io/en/latest",
        "github": "https://github.com/mani-skill/ManiSkill",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "habitat-lab": {
        "description": "Embodied AI simulation platform (navigation, rearrangement)",
        "domain": "reinforcement_learning",
        "category": "simulation",
        "official_docs": "https://aihabitat.org",
        "github": "https://github.com/facebookresearch/habitat-lab",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
