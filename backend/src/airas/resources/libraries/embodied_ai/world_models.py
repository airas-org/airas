# World Models (embodied_ai): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
WORLD_MODELS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "dreamerv3": {
        "description": "Mastering diverse domains with world models (DreamerV3)",
        "domain": "embodied_ai",
        "category": "world_models",
        "official_docs": "https://github.com/danijar/dreamerv3",
        "github": "https://github.com/danijar/dreamerv3",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "tdmpc2": {
        "description": "Scalable model-based RL with world models (TD-MPC2)",
        "domain": "embodied_ai",
        "category": "world_models",
        "official_docs": "https://www.tdmpc2.com",
        "github": "https://github.com/nicklashansen/tdmpc2",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
