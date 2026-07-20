# reinforcement_learning / world_models documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
WORLD_MODELS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "dreamerv3": {
        "description": "Mastering diverse domains with world models (DreamerV3)",
        "domain": "reinforcement_learning",
        "category": "world_models",
        "official_docs": "https://github.com/danijar/dreamerv3",
        "github": "https://github.com/danijar/dreamerv3",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "tdmpc2": {
        "description": "Scalable model-based RL with world models (TD-MPC2)",
        "domain": "reinforcement_learning",
        "category": "world_models",
        "official_docs": "https://www.tdmpc2.com",
        "github": "https://github.com/nicklashansen/tdmpc2",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
